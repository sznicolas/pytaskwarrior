import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.taskwarrior.services.date_calculation_service import DateCalculationService


class TestDateCalculationService(unittest.TestCase):
    def setUp(self):
        self.service = DateCalculationService("task")

    @patch('subprocess.run')
    def test_parse_date_success(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-31T00:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.parse_date("2024-01-31")
        
        self.assertIsInstance(result, datetime)
        mock_run.assert_called_once_with(
            ["task", "calc", "2024-01-31"],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_parse_date_failure(self, mock_run):
        # Mock failed subprocess call
        mock_run.side_effect = Exception("Command failed")

        with self.assertRaises(ValueError):
            self.service.parse_date("invalid-date")

    @patch('subprocess.run')
    def test_calculate_date_success(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-31T12:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.calculate_date("2024-01-31T12:00:00")
        
        self.assertIsInstance(result, datetime)

    @patch('subprocess.run')
    def test_calculate_date_failure(self, mock_run):
        # Mock failed subprocess call
        mock_run.side_effect = Exception("Command failed")

        with self.assertRaises(ValueError):
            self.service.calculate_date("invalid-date")

    @patch('subprocess.run')
    def test_validate_date_valid(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-31T00:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.validate_date("2024-01-31")
        
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_validate_date_invalid(self, mock_run):
        # Mock failed subprocess call
        mock_run.side_effect = Exception("Command failed")

        result = self.service.validate_date("invalid-date")
        
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_get_current_time(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-31T12:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.get_current_time()
        
        self.assertIsInstance(result, datetime)

    @patch('subprocess.run')
    def test_get_today(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-31T00:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.get_today()
        
        self.assertIsInstance(result, datetime)

    @patch('subprocess.run')
    def test_get_tomorrow(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-02-01T00:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.get_tomorrow()
        
        self.assertIsInstance(result, datetime)

    @patch('subprocess.run')
    def test_get_yesterday(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-30T00:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.get_yesterday()
        
        self.assertIsInstance(result, datetime)

    @patch('subprocess.run')
    def test_get_end_of_month(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-31T23:59:59\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.get_end_of_month()
        
        self.assertIsInstance(result, datetime)

    @patch('subprocess.run')
    def test_get_start_of_month(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-01T00:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.get_start_of_month()
        
        self.assertIsInstance(result, datetime)

    @patch('subprocess.run')
    def test_get_start_of_week(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-01-31T00:00:00\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.get_start_of_week()
        
        self.assertIsInstance(result, datetime)

    @patch('subprocess.run')
    def test_get_end_of_week(self, mock_run):
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.stdout = "2024-02-03T23:59:59\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.service.get_end_of_week()
        
        self.assertIsInstance(result, datetime)


if __name__ == '__main__':
    unittest.main()
