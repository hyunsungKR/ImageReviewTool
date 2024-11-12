import unittest
from PySide6.QtCore import QDir
from model import ImageViewerModel

class TestImageViewerModel(unittest.TestCase):
    def setUp(self):
        self.model = ImageViewerModel()
        self.test_folder = "test_folder"
        QDir().mkpath(self.test_folder)

    def tearDown(self):
        QDir(self.test_folder).removeRecursively()

    def test_set_folder(self):
        self.model.set_folder(self.test_folder)
        self.assertEqual(self.model.current_folder, self.test_folder)

    def test_create_cut_folder(self):
        self.model.set_folder(self.test_folder)
        self.model.create_cut_folder()
        self.assertTrue(QDir(self.test_folder + "_cut").exists())

    # 더 많은 테스트 케이스 추가...

if __name__ == '__main__':
    unittest.main()