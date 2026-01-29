import pytest
from mediapipe.tasks.python.vision.face_detector import FaceDetector

from arseille.ml_models.age_estimation.inference import AgeEstimator
from arseille.vending.data import DetectionMetadata
from arseille.vending.enums import VendingMode
from arseille.vending.exceptions import InvalidCameraIndex, InvalidVendingMode
from arseille.vending.utils import TaskExecutor
from arseille.vending.vending_machine import VendingMachine, VideoSource
from tests.utils import DummyVendingMachine  # ty: ignore[unresolved-import]


def test_video_source_invalid_camera_index() -> None:
    with pytest.raises(InvalidCameraIndex):
        VideoSource(999)


def test_vending_machine_factory_creation() -> None:
    vm = VendingMachine.create_default()

    assert isinstance(vm, VendingMachine)
    assert isinstance(vm.video_source, VideoSource)
    assert isinstance(vm.face_detector, FaceDetector)
    assert isinstance(vm.age_estimator, AgeEstimator)
    assert isinstance(vm.task_executor, TaskExecutor)
    assert isinstance(vm._metadata_obj, DetectionMetadata)

    vm.cleanup()


@pytest.mark.anyio
async def test_vending_machine_invalid_mode(
    dummy_vending_machine: DummyVendingMachine,
) -> None:
    with pytest.raises(InvalidVendingMode):
        dummy_vending_machine.set_mode(-1)


@pytest.mark.anyio
async def test_vending_machine_context_manager(
    dummy_vending_machine: DummyVendingMachine,
) -> None:
    assert dummy_vending_machine._lock.locked() is False
    dummy_vending_machine.set_mode(VendingMode.CHECKPOINT_50)

    async with dummy_vending_machine as vm:
        assert vm._lock.locked() is True
        vm._metadata_obj.age = 10
        vm._metadata_obj.timestamp = 123456

    assert vm._metadata_obj.age is None
    assert vm._metadata_obj.timestamp is None
    assert vm._lock.locked() is False
