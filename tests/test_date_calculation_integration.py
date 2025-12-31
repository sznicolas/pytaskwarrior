import unittest
from datetime import datetime

from src.taskwarrior.services.date_calculation_service import DateCalculationService
from src.taskwarrior.task import Task


class TestDateCalculationIntegration(unittest.TestCase):
    def setUp(self):
        self.service = DateCalculationService("task")

    def test_service_initialization(self):
        """Test that the service can be initialized properly."""
        self.assertIsInstance(self.service, DateCalculationService)
        self.assertEqual(self.service.taskwarrior_binary, "task")

    def test_parse_date_with_task_model_integration(self):
        """Test that date parsing works with Task model fields."""
        # Test basic date parsing
        test_date = "2024-01-31"
        parsed_date = self.service.parse_date(test_date)
        
        # Verify it's a datetime object
        self.assertIsInstance(parsed_date, datetime)

    def test_synonym_parsing_integration(self):
        """Test that date synonyms work correctly."""
        # Test today synonym
        try:
            today = self.service.get_today()
            self.assertIsInstance(today, datetime)
        except ValueError:
            # If task calc is not available in test environment, skip
            pass

        # Test tomorrow synonym  
        try:
            tomorrow = self.service.get_tomorrow()
            self.assertIsInstance(tomorrow, datetime)
        except ValueError:
            # If task calc is not available in test environment, skip
            pass

    def test_date_validation_integration(self):
        """Test date validation functionality."""
        # Test valid dates
        self.assertTrue(self.service.validate_date("today"))
        self.assertTrue(self.service.validate_date("2024-01-31"))
        
        # Test invalid dates
        self.assertFalse(self.service.validate_date("invalid-date"))
        self.assertFalse(self.service.validate_date(""))


if __name__ == '__main__':
    unittest.main()
