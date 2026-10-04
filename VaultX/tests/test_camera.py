import pytest

np = pytest.importorskip("numpy")

from bovedafacial.face.camera import CameraError, FileCamera, default_camera, list_v4l2_devices


def test_filecamera_cycles_frames():
    a = np.zeros((4, 4, 3), np.uint8)
    b = np.ones((4, 4, 3), np.uint8)
    cam = FileCamera([a, b]).open()
    assert np.array_equal(cam.read(), a)
    assert np.array_equal(cam.read(), b)
    assert np.array_equal(cam.read(), a)  # vuelve a empezar


def test_filecamera_returns_copies():
    a = np.zeros((2, 2, 3), np.uint8)
    cam = FileCamera([a]).open()
    frame = cam.read()
    frame[0, 0, 0] = 255
    assert a[0, 0, 0] == 0  # el original no se toca


def test_filecamera_empty():
    with pytest.raises(CameraError):
        FileCamera([]).open()


def test_filecamera_context_manager():
    with FileCamera([np.zeros((2, 2, 3), np.uint8)]) as cam:
        assert cam.read().shape == (2, 2, 3)


def test_list_v4l2_devices_is_list():
    assert isinstance(list_v4l2_devices(), list)


def test_default_camera_without_devices(monkeypatch):
    monkeypatch.setattr("bovedafacial.face.camera.list_v4l2_devices", lambda: [])
    with pytest.raises(CameraError):
        default_camera()
