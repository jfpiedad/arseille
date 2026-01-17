import torch
import torch.nn.functional as F
from torch import nn


class MultiBoxLoss(nn.Module):
    def __init__(
        self,
        jaccard_thresh: float = 0.5,
        negpos_ratio: int = 3,
        device: torch.device = torch.device("cpu"),
        dbox_list: torch.Tensor | None = None,
    ) -> None:
        """Initialize MultiBoxLoss.

        Args:
            jaccard_thresh (float, optional): Jaccard threshold. Defaults to 0.5.
            neg_pos (int, optional): Negative-positive ratio. Defaults to 3.
            device (str, optional): Device to use. Defaults to 'cpu'.
            dbox_list (torch.Tensor, optional): Default box list. Defaults to None.
        """
        super().__init__()

        self.jaccard_thresh = jaccard_thresh
        self.negpos_ratio = negpos_ratio
        self.device = device
        self.dbox_list = dbox_list

    def forward(
        self, predictions: torch.Tensor, targets: list[torch.Tensor]
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass for MultiBoxLoss.

        Args:
            predictions (torch.Tensor): Predictions from the model.
            targets (list): Ground truth targets.

        Returns:
            tuple: Localization loss and confidence loss.
        """

        localization_data = predictions[:, :, :4]
        confidence_data = predictions[:, :, 4:]

        batch_size = localization_data.size(0)
        dbox_size = localization_data.size(1)
        class_size = confidence_data.size(2)

        confidence_target_label = torch.zeros(
            (batch_size, dbox_size), dtype=torch.int64, device=self.device
        )
        localization_target = torch.zeros(
            (batch_size, dbox_size, 4), dtype=torch.float32, device=self.device
        )

        for index in range(batch_size):
            if len(targets[index]) > 0:
                truth_boxes = targets[index][:, :-1].to(self.device)
                truth_labels = targets[index][:, -1].to(self.device)

                dbox = self.dbox_list.to(self.device)  # ty: ignore[possibly-missing-attribute], Pytorch
                variances = [0.1, 0.2]

                match_boxes(
                    threshold=self.jaccard_thresh,
                    truth_boxes=truth_boxes,
                    prior_boxes=dbox,
                    variances=variances,
                    labels=truth_labels,
                    localization_targets=localization_target,
                    confidence_targets=confidence_target_label,
                    index=index,
                )

        positive_mask = confidence_target_label > 0
        positive_index = positive_mask.unsqueeze(positive_mask.dim()).expand_as(
            localization_data
        )

        localization_prediction = localization_data[positive_index].view(-1, 4)
        localization_target = localization_target[positive_index].view(-1, 4)

        localization_loss = F.smooth_l1_loss(
            input=localization_prediction, target=localization_target, reduction="sum"
        )

        confidences = confidence_data.view(-1, class_size)

        confidence_loss = F.cross_entropy(
            input=confidences,
            target=torch.clamp(confidence_target_label.view(-1), 0, class_size - 1),
            reduction="none",
        )
        confidence_loss = confidence_loss.view(batch_size, -1)
        confidence_loss[positive_mask] = 0

        num_positives = positive_mask.long().sum(1, keepdim=True)

        _, loss_index = confidence_loss.sort(1, descending=True)
        _, index_rank = loss_index.sort(1)

        num_negatives = torch.clamp(num_positives * self.negpos_ratio, max=dbox_size)

        negative_mask = index_rank < (num_negatives).expand_as(index_rank)

        positive_index_mask = positive_mask.unsqueeze(2).expand_as(confidence_data)
        negative_index_mask = negative_mask.unsqueeze(2).expand_as(confidence_data)

        confidence_hnm = confidence_data[
            (positive_index_mask + negative_index_mask).gt(0)
        ].view(-1, class_size)

        confidence_target_label_hnm = confidence_target_label[
            (positive_mask + negative_mask).gt(0)
        ]

        confidence_loss = F.cross_entropy(
            confidence_hnm,
            torch.clamp(confidence_target_label_hnm, 0, class_size - 1),
            reduction="sum",
        )

        N = num_positives.sum()

        localization_loss /= N
        confidence_loss /= N

        return localization_loss, confidence_loss


def od_collate_fn(batch: list[tuple]) -> tuple[torch.Tensor, list[torch.FloatTensor]]:
    """Collate function for object detection."""

    images = []
    targets = []

    for image, target in batch:
        images.append(image)
        targets.append(torch.FloatTensor(target))

    images = torch.stack(images, dim=0)

    return images, targets


def encode_boxes(
    matched_boxes: torch.Tensor, prior_boxes: torch.Tensor, variances: list[float]
) -> torch.Tensor:
    """
    Encode the variances from the priorbox layers into the ground truth boxes
    we have matched (based on jaccard overlap) with the prior boxes.
    """

    center_offsets = (matched_boxes[:, :2] + matched_boxes[:, 2:]) / 2
    center_offsets = center_offsets - prior_boxes[:, :2]
    center_offsets /= variances[0] * prior_boxes[:, 2:]

    width_height_offsets = matched_boxes[:, 2:] - matched_boxes[:, :2]
    width_height_offsets = width_height_offsets / prior_boxes[:, 2:]
    width_height_offsets = torch.log(width_height_offsets) / variances[1]

    encoded_boxes = torch.cat([center_offsets, width_height_offsets], 1)

    return encoded_boxes


def jaccard(truth_boxes: torch.Tensor, prior_boxes: torch.Tensor) -> torch.Tensor:
    """
    Compute the jaccard overlap of two sets of boxes. The jaccard overlap
    is simply the intersection over union of two boxes. Here we operate on
    ground truth boxes and default boxes.
    """

    intersection = intersect(truth_boxes, prior_boxes)

    truth_boxes_area = (
        (
            (truth_boxes[:, 2] - truth_boxes[:, 0])
            * (truth_boxes[:, 3] - truth_boxes[:, 1])
        )
        .unsqueeze(1)
        .expand_as(intersection)
    )

    prior_boxes_area = (
        (
            (prior_boxes[:, 2] - prior_boxes[:, 0])
            * (prior_boxes[:, 3] - prior_boxes[:, 1])
        )
        .unsqueeze(0)
        .expand_as(intersection)
    )

    union = truth_boxes_area + prior_boxes_area - intersection

    return intersection / union


def point_form(prior_boxes: torch.Tensor) -> torch.Tensor:
    """
    Convert prior_boxes to (xmin, ymin, xmax, ymax) representation for comparison
    to point form ground truth data.
    """

    return torch.cat(
        (
            prior_boxes[:, :2] - prior_boxes[:, 2:] / 2,
            prior_boxes[:, :2] + prior_boxes[:, 2:] / 2,
        ),
        dim=1,
    )


def intersect(bbox_a: torch.Tensor, bbox_b: torch.Tensor) -> torch.Tensor:
    """
    Resize both tensors to [A, B, 2] without new malloc and compute the area
    of intersection between box_a and box_b.
    """

    A = bbox_a.size(0)
    B = bbox_b.size(0)

    min_xy = torch.max(
        bbox_a[:, :2].unsqueeze(1).expand(A, B, 2),
        bbox_b[:, :2].unsqueeze(0).expand(A, B, 2),
    )

    max_xy = torch.min(
        bbox_a[:, 2:].unsqueeze(1).expand(A, B, 2),
        bbox_b[:, 2:].unsqueeze(0).expand(A, B, 2),
    )

    intersection = torch.clamp((max_xy - min_xy), min=0)

    return intersection[:, :, 0] * intersection[:, :, 1]


def match_boxes(
    threshold: float,
    truth_boxes: torch.Tensor,
    prior_boxes: torch.Tensor,
    variances: list[float],
    labels: torch.Tensor,
    localization_targets: torch.Tensor,
    confidence_targets: torch.Tensor,
    index: int,
) -> None:
    """
    Match each prior box with the ground truth box of the highest jaccard
    overlap, encode the bounding boxes, then return the matched indices
    corresponding to both confidence and location preds.
    """

    overlaps = jaccard(truth_boxes, point_form(prior_boxes))

    best_prior_overlap, best_prior_index = overlaps.max(1, keepdim=True)
    best_truth_overlap, best_truth_index = overlaps.max(0, keepdim=True)

    best_truth_index.squeeze_(0)
    best_truth_overlap.squeeze_(0)

    best_prior_index.squeeze_(1)
    best_prior_overlap.squeeze_(1)

    best_truth_overlap.index_fill_(0, best_prior_index, 2)

    for index in range(best_prior_index.size(0)):
        best_truth_index[best_prior_index[index]] = index

    matches = truth_boxes[best_truth_index]

    confidence = labels[best_truth_index] + 1
    confidence[best_truth_overlap < threshold] = 0

    localization = encode_boxes(matches, prior_boxes, variances)

    localization_targets[index] = localization
    confidence_targets[index] = confidence
