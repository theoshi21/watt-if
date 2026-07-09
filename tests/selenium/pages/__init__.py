"""Page Object Model classes for the WATT-IF Selenium automation test suite.

All page objects extend BasePage and encapsulate locators and interaction
methods for their respective application pages/components.
"""

from tests.selenium.pages.base_page import BasePage
from tests.selenium.pages.login_page import LoginPage
from tests.selenium.pages.register_page import RegisterPage
from tests.selenium.pages.dashboard_page import DashboardPage
from tests.selenium.pages.forecast_page import ForecastPage
from tests.selenium.pages.ask_page import AskPage
from tests.selenium.pages.data_entry_page import DataEntryPage
from tests.selenium.pages.price_calculator_page import PriceCalculatorPage
from tests.selenium.pages.account_settings_page import AccountSettingsPage
from tests.selenium.pages.sidebar import Sidebar
from tests.selenium.pages.top_bar import TopBar

__all__ = [
    "BasePage",
    "LoginPage",
    "RegisterPage",
    "DashboardPage",
    "ForecastPage",
    "AskPage",
    "DataEntryPage",
    "PriceCalculatorPage",
    "AccountSettingsPage",
    "Sidebar",
    "TopBar",
]
