import contextlib

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, MoveTargetOutOfBoundsException
from selenium.webdriver.remote.webelement import WebElement

import extended_expected_conditions as eec
from wait import ActionWait


class BasePage(object):

    def __init__(self, driver, implicit_wait=30):
        """

        :param driver:
        :param implicit_wait:
        :return:
        """
        self._driver = driver
        self._implicit_wait = implicit_wait

    def __getattr__(self, item):
        """

        :param item:
        :return:
        """
        return getattr(self.driver, item)

    @property
    def driver(self):
        return self._driver

    def click(self, locator, params=None, timeout=None):
        """
        Click web element.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element
        :return: None
        """
        self._click(locator, params, timeout)

    def alt_click(self, locator, params=None, timeout=None):
        """
        Alt-click web element.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element
        :return: None
        """
        self._click(locator, params, timeout, Keys.ALT)

    def shift_click(self, locator, params=None, timeout=None):
        """
        Shift-click web element.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element
        :return: None
        """
        self._click(locator, params, timeout, Keys.SHIFT)

    def multi_click(self, locator, params=None, timeout=None):
        """
        Presses left control or command button depending on OS, clicks and then releases control or command key.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element
        :return: None
        """
        multi_key = Keys.LEFT_CONTROL if 'explorer' in self.driver.name else Keys.COMMAND
        self._click(locator, params, timeout, multi_key)

    def _click(self, locator, params=None, timeout=None, key=None):
        element = locator
        if not isinstance(element, WebElement):
            element = self._get(locator, ec.element_to_be_clickable, params, timeout, "Element was never clickable!")

        if key is not None:
            ActionChains(self.driver).key_down(key).click(element).key_up(key).perform()
        else:
            element.click()

    def shift_select(self, first_element, last_element):
        """
        Clicks a web element and shift clicks another web element.

        :param first_element: WebElement instance
        :param last_element: WebElement instance
        :return: None
        """
        self.click(first_element)
        self.shift_click(last_element)

    def multi_select(self, elements_to_select):
        """
        Multi-select any number of elements.

        :param elements_to_select: list of WebElement instances
        :return: None
        """
        # Click the first element
        first_element = elements_to_select.pop()
        self.click(first_element)

        # Click the rest
        for index, element in enumerate(elements_to_select, start=1):
            self.multi_click(element)

    def select_from_drop_down_by_value(self, locator, value, params=None):
        """
        Select option from drop down widget using value.

        :param locator: locator tuple or WebElement instance
        :param value: string
        :param params: (optional) locator parameters
        :return: None
        """
        from selenium.webdriver.support.ui import Select

        element = locator
        if not isinstance(element, WebElement):
            element = self.get_present_element(locator, params)

        Select(element).select_by_value(value)

    def select_from_drop_down_by_text(self, drop_down_locator, option_locator, option_text, params=None):
        """
        Select option from drop down widget using text.

        :param drop_down_locator: locator tuple (if any, params needs to be in place) or WebElement instance
        :param option_locator: locator tuple (if any, params needs to be in place)
        :param option_text: text to base option selection on
        :param params: Dictionary containing dictionary of params
        :return: None
        """
        # Open/activate drop down
        self.click(drop_down_locator, params['drop_down'])

        # Get options
        for option in self.get_present_elements(option_locator, params['option']):
            if self.get_text(option) == option_text:
                self.click(option)
                break

    def select_from_drop_down_by_locator(self, drop_down_locator, option_locator, params=None):
        """
        Select option from drop down widget using locator.

        :param drop_down_locator: locator tuple or WebElement instance
        :param option_locator: locator tuple or WebElement instance
        :param params: Dictionary containing dictionary of params
        :return: None
        """
        # Open/activate drop down
        self.click(drop_down_locator, params['drop_down'])

        # Click option in drop down
        self.click(option_locator, params['option'])

    def get_attribute(self, locator, attribute, params=None, timeout=None, visible=False):
        """
        Get attribute from element based on locator with optional parameters.

        Calls get_element() with expected condition: visibility of element located

        :param locator: locator tuple or WebElement instance
        :param attribute: attribute to return
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for text (default: None)
        :param visible: should element be visible before getting text (default: False)
        :return: element attribute
        """
        element = locator
        if not isinstance(element, WebElement):
            element = self.get_present_element(locator, params, timeout, visible)
        try:
            return element.get_attribute(attribute)
        except AttributeError:
            msg = "Element with attribute <{}> was never located!".format(attribute)
            raise NoSuchElementException(msg)

    def get_text(self, locator, params=None, timeout=None, visible=True):
        """
        Get text or value from element based on locator with optional parameters.

        :param locator: element identifier
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for text (default: None)
        :param visible: should element be visible before getting text (default: True)
        :return: element text, value or empty string
        """
        element = locator
        if not isinstance(element, WebElement):
            element = self.get_present_element(locator, params, timeout, visible)

        if element.text:
            return element.text
        else:
            try:
                return element.get_attribute('value')
            except AttributeError:
                return ""

    def enter_text(self, locator, text, with_click=True, with_clear=False, with_enter=False, params=None):
        """
        Enter text into a web element.

        :param locator: locator tuple or WebElement instance
        :param text: text to input
        :param with_click: clicks the input field
        :param with_clear: clears the input field
        :param with_enter: hits enter-key after text input
        :param params: (optional) locator params
        :return: None
        """
        element = locator
        if not isinstance(element, WebElement):
            element = self.get_visible_element(locator, params)

        if with_click:
            self.click(element)

        actions = ActionChains(self.driver)
        actions.send_keys_to_element(element, text)

        if with_clear:
            element.clear()

        if with_enter:
            actions.send_keys(Keys.ENTER)

        actions.perform()

    def drag_and_drop(self, source_element, target_element, params=None):
        """
        Drag source element and drop at target element.

        Note: Target can either be a WebElement or a list with x- and y-coordinates (integers)

        :param source_element: WebElement instance
        :param target_element: WebElement instance or list of x- and y-coordinates
        :param params: Dictionary containing dictionary of params
        :return: None
        """
        if not isinstance(source_element, WebElement):
            source_element = self.get_visible_element(source_element, params['source'])
        if not isinstance(target_element, WebElement) and not isinstance(target_element, list):
            source_element = self.get_visible_element(target_element, params['target'])

        action = ActionChains(self.driver)
        if isinstance(target_element, WebElement):
            action.drag_and_drop(source_element, target_element)
        else:
            action.click_and_hold(source_element).move_by_offset(*target_element).release()

        action.perform()

    def get_element_with_text(self, locator, text, params=None, timeout=None, visible=False):
        """
        Get element that contains the text <text> either by text or by attribute value.

        :param locator: locator tuple or list of WebElements
        :param text: text that the element should contain
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :param visible: (optional) if the element should also be visible (default: False)
        :return: WebElement instance
        """
        elements = locator
        if not isinstance(elements, list):
            elements = self.get_present_elements(elements, params, timeout, visible)

        for element in elements:
            element_text = self.get_text(element)
            if element_text is not None and text in element_text.strip():
                return element
            else:
                attrib = element.get_attribute('value')
                if attrib is not None and text in attrib.strip():
                    return element

        if timeout == 0:
            return None  # Element with text was not present, and since timeout == 0 we don't wish to fail.

        if isinstance(locator, list):
            msg = "None of the elements had the text: {}".format(text)
        else:
            msg = "Element with type <{}>, locator <{}> and text <{text}> was never located!".format(*locator, text=text)
        raise NoSuchElementException(msg)

    def get_present_element(self, locator, params=None, timeout=None, visible=False):
        """
        Get element present in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param locator: element identifier
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :param visible: (optional) if the element should also be visible (default: False)
        :return: WebElement instance
        """
        expected_condition = ec.visibility_of_element_located if visible else ec.presence_of_element_located
        return self._get(locator, expected_condition, params, timeout, error_msg="Element was never present!")

    def get_visible_element(self, locator, params=None, timeout=None):
        """
        Get element both present AND visible in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param locator: locator tuple
        :param params: (optional) locator params
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :return: WebElement instance
        """
        return self.get_present_element(locator, params, timeout, True)

    def get_present_elements(self, locator, params=None, timeout=None, visible=False):
        """
        Get element present in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param locator: element identifier
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :param visible: (optional) if the element should also be visible (default: False)
        :return: WebElement instance
        """
        expected_condition = eec.visibility_of_all_elements_located if visible else ec.presence_of_all_elements_located
        return self._get(locator, expected_condition, params, timeout, error_msg="Element was never present!")

    def get_visible_elements(self, locator, params=None, timeout=None):
        """
        Get element both present AND visible in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param locator: locator tuple
        :param params: (optional) locator params
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :return: WebElement instance
        """
        return self.get_present_elements(locator, params, timeout, True)

    def _get(self, locator, expected_condition, params=None, timeout=None, error_msg="", **kwargs):
        """
        Get elements based on locator with optional parameters.

        Uses selenium.webdriver.support.expected_conditions to determine the state of the element(s).

        :param locator: element identifier
        :param expected_condition: expected condition of element (ie. visible, clickable, etc)
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :param kwargs: optional arguments to expected conditions
        :return: WebElement instance, list of WebElements, or None
        """
        from selenium.webdriver.support.ui import WebDriverWait

        if not isinstance(locator, WebElement):
            error_msg += "\nLocator of type <{}> with selector <{}> with params <{params}>".format(*locator, params=params)
            locator = BasePage.get_compliant_locator(*locator, params=params)

        exp_cond = expected_condition(locator, **kwargs)
        if timeout == 0:
            try:
                return exp_cond(self.driver)
            except NoSuchElementException:
                return None

        if timeout is None:
            timeout = self._implicit_wait

        error_msg += "\nExpected condition: {}" \
                     "\nTimeout: {}".format(expected_condition, timeout)

        return WebDriverWait(self.driver, timeout).until(exp_cond, error_msg)

    def get_present_child(self, parent, locator, params=None, timeout=None, visible=False):
        """

        :param parent:
        :param locator:
        :param params:
        :param timeout:
        :param visible:
        :return:
        """
        expected_condition = eec.visibility_of_child_located if visible else eec.presence_of_child_located
        return self._get_child(parent, locator, expected_condition, params, timeout)

    def get_visible_child(self, parent, locator, params=None, timeout=None):
        """

        :param parent:
        :param locator:
        :param params:
        :param timeout:
        :return:
        """
        return self.get_present_child(parent, locator, params, timeout, True)

    def get_present_children(self, parent, locator, params=None, timeout=None, visible=False):
        """

        :param parent:
        :param locator:
        :param params:
        :param timeout:
        :param visible:
        :return:
        """
        expected_condition = eec.visibility_of_all_children_located if visible else eec.presence_of_all_children_located
        return self._get_child(parent, locator, expected_condition, params, timeout)

    def get_visible_children(self, parent, locator, params=None, timeout=None):
        """

        :param parent:
        :param locator:
        :param params:
        :param timeout:
        :return:
        """
        return self.get_present_children(parent, locator, params, timeout, True)

    def _get_child(self, parent, locator, expected_condition, params=None, timeout=None, error_msg=''):
        """

        :param parent:
        :param locator:
        :param expected_condition:
        :param params:
        :param timeout:
        :param error_msg:
        :return:
        """
        return self._get(locator, expected_condition, params, timeout, error_msg, parent=parent)

    @staticmethod
    def get_compliant_locator(by, locator, params=None):
        """
        Returns a tuple of by and locator prepared with optional parameters.

        :param by: Type of locator (ie. CSS, ClassName, etc)
        :param locator: element locator
        :param params: (optional) locator parameters
        :return: tuple of by and locator with optional parameters
        """
        from selenium.webdriver.common.by import By

        if params is not None and not isinstance(params, dict):
            raise TypeError("<params> need to be of type <dict>, was <{}>".format(params.__class__.__name__))

        return getattr(By, by), locator.format(**(params if params else {}))

    def scroll_element_into_view(self, selector):
        """
        Scrolls an element into view.

        :param selector: selector of element to scroll into view
        :return: None
        """
        self.execute_sync_script("$('{}')[0].scrollIntoView( true );".format(selector))

    def open_hover(self, locator, params=None):
        """
        Open a hover or popover.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :return: element hovered
        """
        element = locator
        if not isinstance(element, WebElement):
            element = self.get_visible_element(locator, params)
        ActionChains(self.driver).move_to_element(element).perform()
        return element

    def close_hover(self, element):
        """
        Close hover by moving to a set offset "away" from the element being hovered.

        :param element: element that triggered the hover to open
        :return: None
        """
        try:
            ActionChains(self.driver).move_to_element_with_offset(element, -100, -100).perform()
        except (StaleElementReferenceException, MoveTargetOutOfBoundsException):
            return True  # Means the hover is already closed or otherwise gone

    def perform_hover_action(self, locator, func, error_msg='', exceptions=None, params=None, **kwargs):
        """
        Hovers an element and performs whatever action is specified in the supplied function.

        NOTE: Specified function MUST return a non-false value upon success!

        :param locator: locator tuple or WebElement instance
        :param func: action to perform while hovering
        :param error_msg: error message to display if hovering failed
        :param exceptions: list of exceptions (default: StaleElementReferenceException)
        :param params: (optional) locator parameters
        :param kwargs: keyword arguments to the function func
        :return: result of performed action
        """
        def _do_hover():
            try:
                with self.hover(locator, params):
                    return func(**kwargs)
            except exc:
                return False

        exc = [StaleElementReferenceException]
        if exceptions is not None:
            try:
                exc.extend(iter(exceptions))
            except TypeError:  # exceptions is not iterable
                exc.append(exceptions)
        exc = tuple(exc)

        msg = error_msg if error_msg else "Performing hover actions failed!"
        return ActionWait().until(_do_hover, msg)

    @contextlib.contextmanager
    def hover(self, locator, params=None):
        """
        Context manager for hovering.

        Opens and closes the hover.

        Usage:
            with self.hover(locator, params):
                // do something with the hover

        :param locator: locator tuple
        :param params: (optional) locator params
        :return: None
        """
        # Open hover
        element = self.open_hover(locator, params)
        try:
            yield
        finally:
            # Close hover
            self.close_hover(element)

    def wait_for_element_to_disappear(self, locator, params=None, timeout=None):
        """
        Waits until the element is not visible (hidden) or no longer attached to the DOM.

        Raises TimeoutException if element does not become invisible.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator params
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :return: None
        """
        exp_cond = eec.invisibility_of if isinstance(locator, WebElement) else ec.invisibility_of_element_located
        try:
            self._get(locator, exp_cond, params, timeout, error_msg="Element never disappeared")
        except (StaleElementReferenceException, NoSuchElementException):
            return True  # Element was not present, ie disappeared was satisfied

    def wait_for_non_empty_text(self, locator, params=None, timeout=5):
        """
        Wait and get elements when they're populated with any text.

        :param locator: locator tuple
        :param params: (optional) locator params
        :param timeout: (optional) maximum waiting time (in seconds) (default: 5)
        :return: list of WebElements
        """
        def _do_wait():
            elements = self.get_present_elements(locator, params)
            for element in elements:
                if not self.get_text(element):
                    return False
            return elements

        return ActionWait(timeout).until(_do_wait, "Element text was never populated!")

    def wait_for_attribute(self, locator, attribute, value, params=None, timeout=5):
        """
        Waits for an element attribute to get a certain value.

        Note: This function re-get's the element in a loop to avoid caching or stale element issues.

        :Example:
            Wait for the class attribute to get 'board-hidden' value

        :param locator: locator tuple
        :param attribute: element attribute
        :param value: attribute value to wait for
        :param params: (optional) locator params
        :param timeout: (optional) maximum waiting time (in seconds) (default: 5)
        :return: None
        """
        def _do_wait():
            element = self.get_present_element(locator, params)
            return value in self.get_attribute(element, attribute)

        ActionWait(timeout).until(_do_wait, "Attribute never set!")

    def wait_for_zero_queries(self, timeout=5):
        """
        Waits until there are no active or pending API requests.

        Raises TimeoutException should silence not be had.

        :param timeout: time to wait for silence (default: 5 seconds)
        :return: None
        """
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, timeout).until(lambda s: s.execute_script("return jQuery.active === 0"))