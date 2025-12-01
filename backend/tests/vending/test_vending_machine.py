import pytest
from mediapipe.tasks.python.vision.face_detector import FaceDetector

from arseille.exceptions import InvalidCameraIndex, InvalidVendingMode
from arseille.ml_models.age_estimation.inference import AgeEstimator
from arseille.vending.data import DetectionMetadata
from arseille.vending.modes import VendingMode
from arseille.vending.utils import TaskExecutor
from arseille.vending.vending_machine import VendingMachine, VideoSource


def test_video_source_invalid_camera_index() -> None:
    with pytest.raises(InvalidCameraIndex):
        VideoSource(999)


def test_vending_machine_factory_creation() -> None:
    vm = VendingMachine.create_standard()

    assert isinstance(vm, VendingMachine)
    assert isinstance(vm.video_source, VideoSource)
    assert isinstance(vm.face_detector, FaceDetector)
    assert isinstance(vm.age_estimator, AgeEstimator)
    assert isinstance(vm.task_executor, TaskExecutor)
    assert isinstance(vm.metadata_obj, DetectionMetadata)

    vm.cleanup()


@pytest.mark.anyio
async def test_vending_machine_invalid_mode(
    dummy_vending_machine: VendingMachine,
) -> None:
    dummy_vending_machine.set_mode(-1)

    with pytest.raises(InvalidVendingMode):
        await dummy_vending_machine.set_unavailable()


@pytest.mark.anyio
async def test_vening_machine_availability(
    dummy_vending_machine: VendingMachine,
) -> None:
    assert dummy_vending_machine._lock.locked() is False

    with pytest.raises(InvalidVendingMode):
        await dummy_vending_machine.set_unavailable()

    dummy_vending_machine.set_mode(VendingMode.CHECKPOINT_25)

    await dummy_vending_machine.set_unavailable()
    assert dummy_vending_machine._lock.locked() is True

    dummy_vending_machine.set_available()
    assert dummy_vending_machine._lock.locked() is False
