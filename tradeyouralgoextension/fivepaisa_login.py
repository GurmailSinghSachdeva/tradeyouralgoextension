"""
5paisa Vendor Login Automation using Playwright
"""
import asyncio
import json
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional
import logging
from urllib.parse import urlparse, parse_qs
import re

from .config import (
    FIVEPAISA_MOBILE_NUMBER,
    FIVEPAISA_OTP,
    FIVEPAISA_PIN,
    FIVEPAISA_VENDOR_LOGIN_URL,
    FIVEPAISA_RESPONSE_URL,
    HEADLESS,
    TIMEOUT,
    OTP_API_URL,
    OTP_API_ENABLED,
)
from .otp_api_client import OTPAPIClient

logger = logging.getLogger(__name__)


class FivePaisaLogin:
    """Handles vendor login to 5paisa and extracts access token from redirect URL"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.access_token: Optional[str] = None

    async def start_browser(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=HEADLESS)
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        self.page = await context.new_page()
        logger.info("Browser started successfully")

    async def login(self) -> Optional[str]:
        """
        Perform vendor login to 5paisa and extract access token from redirect URL
        
        Flow:
        1. Navigate to vendor login URL
        2. Enter mobile number
        3. Wait for manual OTP entry (or use FIVEPAISA_OTP if provided)
        4. Enter PIN
        5. Wait for redirect to ResponseURL (tradeyouralgo.com)
        6. Extract access token from redirect URL
        
        Returns:
            Access token string if login successful, None otherwise
        """
        if not self.page:
            await self.start_browser()

        try:
            # Step 1: Navigate to vendor login URL
            logger.info(f"Navigating to vendor login URL: {FIVEPAISA_VENDOR_LOGIN_URL}")
            await self.page.goto(FIVEPAISA_VENDOR_LOGIN_URL, timeout=TIMEOUT)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)  # Wait for page to fully load

            # Step 2: Enter mobile number
            logger.info("Waiting for mobile number input field...")
            # Try multiple selectors for mobile number input
            mobile_selectors = [
                'input[placeholder*="MOBILE"], input[placeholder*="Mobile"], input[placeholder*="mobile"]',
                'input[name*="mobile"], input[name*="phone"], input[name*="Mobile"]',
                'input[type="tel"]',
                'input[id*="mobile"], input[id*="phone"]',
            ]
            
            mobile_input = None
            mobile_selector_found = None
            for selector in mobile_selectors:
                try:
                    mobile_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if mobile_input:
                        mobile_selector_found = selector
                        break
                except:
                    continue
            
            if not mobile_input or not mobile_selector_found:
                raise Exception("Could not find mobile number input field")
            
            await self.page.fill(mobile_selector_found, FIVEPAISA_MOBILE_NUMBER)
            logger.info(f"Mobile number entered: {FIVEPAISA_MOBILE_NUMBER}")

            # Click proceed/submit button after entering mobile
            proceed_selectors = [
                'button:has-text("Proceed")',
                'button[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Send OTP")',
            ]
            
            for btn_selector in proceed_selectors:
                try:
                    btn = await self.page.wait_for_selector(btn_selector, timeout=3000)
                    if btn:
                        await self.page.click(btn_selector)
                        logger.info("Proceed button clicked")
                        break
                except:
                    continue

            # Wait for OTP input field to appear
            await asyncio.sleep(2)
            await self.page.wait_for_load_state("networkidle")
            logger.info("Waiting for OTP input field...")
            
            # DEBUG: Capture page structure for OTP field
            await self._debug_page_structure("otp_screen")
            
            # OTP is entered in 6 separate input fields: dvLoginMPINOTP1 through dvLoginMPINOTP6
            otp_field_ids = ['dvLoginMPINOTP1', 'dvLoginMPINOTP2', 'dvLoginMPINOTP3', 
                            'dvLoginMPINOTP4', 'dvLoginMPINOTP5', 'dvLoginMPINOTP6']
            
            # Wait for first OTP field to appear
            try:
                await self.page.wait_for_selector(f'#{otp_field_ids[0]}', timeout=10000)
                logger.info("OTP input fields found")
            except:
                # DEBUG: Try to find any input fields on the page
                await self._debug_find_all_inputs("otp_screen")
                raise Exception("Could not find OTP input fields")

            # Step 3: Handle OTP entry
            otp_to_use = None
            
            # Priority: Config OTP → API OTP (from Make) → Manual entry
            if FIVEPAISA_OTP:
                # Use OTP from config if provided
                otp_to_use = FIVEPAISA_OTP.strip()
                logger.info("Using OTP from configuration")
            elif OTP_API_ENABLED:
                # Try to fetch OTP from API (which Make will populate)
                logger.info("=" * 60)
                logger.info("📡 Fetching OTP from API (Make integration)...")
                logger.info("=" * 60)
                
                otp_client = OTPAPIClient(api_url=OTP_API_URL)
                
                # Verify API connection
                if not otp_client.verify_connection():
                    logger.warning(f"⚠️ OTP API server not reachable at {OTP_API_URL}")
                    logger.warning("Make sure the OTP API server is running")
                    logger.warning("Falling back to manual OTP entry")
                else:
                    logger.info("✅ Connected to OTP API server")
                    # Wait for OTP from Make (up to 5 minutes)
                    otp_to_use = otp_client.wait_for_otp(max_wait_seconds=300, check_interval_seconds=2)
                    
                    if otp_to_use:
                        logger.info(f"✅ OTP received from API: {otp_to_use[:2]}**")
                        # Clear OTP after fetching (optional, but good practice)
                        otp_client.clear_otp()
                    else:
                        logger.warning("⚠️ Could not fetch OTP from API, falling back to manual entry")
            
            if otp_to_use:
                # Automated OTP entry
                logger.info("Entering OTP automatically...")
                otp_digits = list(otp_to_use.strip())
                if len(otp_digits) != 6:
                    raise Exception(f"OTP must be 6 digits, got {len(otp_digits)}")
                
                for idx, digit in enumerate(otp_digits):
                    await self.page.fill(f'#{otp_field_ids[idx]}', digit)
                    await asyncio.sleep(0.1)  # Small delay between fields
                logger.info("OTP entered automatically")
            else:
                # Manual OTP entry - wait for user to fill all 6 fields
                logger.info("=" * 60)
                logger.info("⚠️  MANUAL ACTION REQUIRED ⚠️")
                logger.info("Please enter the 6-digit OTP in the browser window")
                logger.info("Waiting for OTP to be entered...")
                logger.info("=" * 60)
                
                # Wait for all 6 OTP fields to be filled
                max_wait_time = 300  # 5 minutes max wait
                wait_interval = 1
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    # Check if all 6 fields have values
                    all_filled = True
                    for field_id in otp_field_ids:
                        value = await self.page.input_value(f'#{field_id}')
                        if not value or value.strip() == '':
                            all_filled = False
                            break
                    
                    if all_filled:
                        logger.info("OTP detected in all fields")
                        break
                    
                    await asyncio.sleep(wait_interval)
                    elapsed_time += wait_interval
                
                if elapsed_time >= max_wait_time:
                    raise Exception("Timeout waiting for OTP entry")

            # Click verify/submit button after OTP entry
            verify_selectors = [
                '#btnVerify',
                'button#btnVerify',
                'button:visible:has-text("Verify")',
                'button:has-text("Submit")',
                'button[type="submit"]',
                'button:has-text("Login")',
            ]
            
            for btn_selector in verify_selectors:
                try:
                    btn = await self.page.wait_for_selector(btn_selector, timeout=5000, state="visible")
                    if btn:
                        await btn.click()
                        logger.info(f"Verify/Submit button clicked after OTP using selector: {btn_selector}")
                        break
                except:
                    continue

            # Wait for PIN screen to appear
            await asyncio.sleep(2)
            await self.page.wait_for_load_state("networkidle")
            
            # DEBUG: Capture PIN screen structure
            await self._debug_page_structure("pin_screen")
            
            # Step 4: Enter PIN
            # PIN is entered in 6 separate password input fields: dvPin1 through dvPin6
            pin_field_ids = ['dvPin1', 'dvPin2', 'dvPin3', 'dvPin4', 'dvPin5', 'dvPin6']
            
            logger.info("Waiting for PIN input fields...")
            try:
                await self.page.wait_for_selector(f'#{pin_field_ids[0]}', timeout=10000)
                logger.info("PIN input fields found")
            except:
                # Check if we're already redirected (PIN might not be required)
                current_url = self.page.url
                if FIVEPAISA_RESPONSE_URL in current_url:
                    logger.info("Already redirected, PIN step may have been skipped")
                else:
                    raise Exception("Could not find PIN input fields")
            
            # Enter PIN digit by digit into each field
            pin_digits = list(FIVEPAISA_PIN.strip())
            if len(pin_digits) != 6:
                raise Exception(f"PIN must be 6 digits, got {len(pin_digits)}")
            
            logger.info("Entering PIN...")
            for idx, digit in enumerate(pin_digits):
                await self.page.fill(f'#{pin_field_ids[idx]}', digit)
                await asyncio.sleep(0.1)  # Small delay between fields
            logger.info("PIN entered")

            # Debug: capture PIN screen and button state before submitting
            try:
                await self.page.screenshot(path="debug_pin_before_click.png", full_page=True)
                logger.info("📸 Saved PIN screen screenshot: debug_pin_before_click.png")
                candidate_btn = await self.page.query_selector('#btnVerificationSubmit')
                if candidate_btn:
                    btn_visible = await candidate_btn.is_visible()
                    btn_enabled = await candidate_btn.is_enabled()
                    btn_text = await candidate_btn.text_content()
                    logger.info(f"Submit button state -> visible: {btn_visible}, enabled: {btn_enabled}, text: {btn_text}")
            except Exception as e:
                logger.debug(f"Could not capture pre-click PIN debug info: {e}")
            
            # Wait a bit for PIN to be processed
            await asyncio.sleep(0.5)

            # Auto-click submit button after PIN entry - try multiple strategies
            pin_submit_selectors = [
                '#btnVerificationSubmit',
                'button#btnVerificationSubmit',
                'button:visible:has-text("Submit")',
                'button:has-text("Proceed")',
                'button[type="submit"]',
                'button:has-text("Verify")',
                'input[type="submit"]',
                'button[id*="submit"]',
                'button[id*="Submit"]',
                'button[class*="submit"]',
                'button[class*="btn"]',
            ]

            button_clicked = False
            for btn_selector in pin_submit_selectors:
                try:
                    btn = await self.page.wait_for_selector(btn_selector, timeout=3000, state="visible")
                    if btn:
                        is_visible = await btn.is_visible()
                        is_enabled = await btn.is_enabled()
                        if is_visible and is_enabled:
                            await btn.click()
                            logger.info(f"Submit button clicked after PIN using selector: {btn_selector}")
                            button_clicked = True
                            break
                except Exception as e:
                    logger.debug(f"Selector {btn_selector} failed: {e}")
                    continue

            if not button_clicked:
                # DEBUG: Find all buttons on the page
                logger.warning("Could not find submit button with standard selectors. Finding all buttons...")
                buttons_info = await self.page.evaluate("""
                    () => {
                        const buttons = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]'));
                        return buttons.map(btn => ({
                            tag: btn.tagName,
                            type: btn.type || null,
                            id: btn.id || null,
                            className: btn.className || null,
                            text: btn.textContent?.trim() || btn.value || null,
                            visible: btn.offsetParent !== null,
                            disabled: btn.disabled || false
                        }));
                    }
                """)

                logger.info("=" * 80)
                logger.info("🔍 DEBUG: All Buttons Found on PIN Screen:")
                logger.info("=" * 80)
                for idx, btn in enumerate(buttons_info, 1):
                    if btn['visible']:  # Only show visible buttons
                        logger.info(f"\nButton #{idx}:")
                        logger.info(f"  Tag: {btn['tag']}")
                        logger.info(f"  Type: {btn['type']}")
                        logger.info(f"  ID: {btn['id']}")
                        logger.info(f"  Class: {btn['className']}")
                        logger.info(f"  Text: {btn['text']}")
                        logger.info(f"  Disabled: {btn['disabled']}")
                logger.info("=" * 80)

                # Try clicking the first visible button that's not disabled
                for btn_info in buttons_info:
                    if btn_info['visible'] and not btn_info['disabled'] and btn_info['text']:
                        try:
                            if btn_info['id']:
                                await self.page.click(f'#{btn_info["id"]}')
                            elif btn_info['text']:
                                await self.page.click(f'button:has-text("{btn_info["text"]}")')
                            logger.info(f"Clicked button: {btn_info['text']}")
                            button_clicked = True
                            break
                        except Exception:
                            continue

                if not button_clicked:
                    logger.error("❌ Could not find or click submit button after PIN entry")
                    await self.page.screenshot(path="pin_submit_error.png")
                    raise Exception("Could not find submit button after PIN entry")

            # Step 5: Wait for backend callback/redirect and extract access token
            logger.info(f"Waiting for backend callback/response at {FIVEPAISA_RESPONSE_URL} (no manual redirect) ...")

            # Normalize target URL for flexible matching (http/https, trailing slash)
            target_substr = FIVEPAISA_RESPONSE_URL.replace("https://", "").replace("http://", "").rstrip("/")

            response_text = None
            try:
                resp = await self.page.wait_for_event(
                    "response",
                    predicate=lambda r: target_substr in r.url.replace("https://", "").replace("http://", ""),
                    timeout=60000  # give the backend enough time to answer
                )
                response_text = await resp.text()
                logger.info(f"Received response from backend callback (first 200 chars): {response_text[:200]}...")
            except Exception as e:
                logger.warning(f"Did not get backend callback response within timeout: {e}")
                logger.info("Continuing without redirect wait; page should stay on 5paisa")

            # Step 6: Extract access token from response text or redirect URL
            self.access_token = None
            if response_text:
                self.access_token = self._extract_token_from_response(response_text)
            
            if self.access_token:
                logger.info("✅ Login successful! Access token obtained.")
                logger.info(f"Token (first 20 chars): {self.access_token[:20]}...")
                return self.access_token
            else:
                logger.error("❌ Login completed but access token not found in backend response body")
                # Take screenshot for debugging
                await self.page.screenshot(path="token_extraction_error.png")
                # Keep the browser open a bit longer so you can manually check
                await asyncio.sleep(30)
                return None

        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            # Take screenshot for debugging
            if self.page:
                await self.page.screenshot(path="login_error.png")
            raise

    def _extract_token_from_url(self, url: str) -> Optional[str]:
        """
        Extract RequestToken from redirect URL query parameters
        
        The token is in the RequestToken parameter:
        https://tradeyouralgo.com/?RequestToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&state=
        
        Args:
            url: The redirect URL containing the RequestToken
            
        Returns:
            RequestToken string if found, None otherwise
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Primary token parameter name (5paisa uses RequestToken)
            if 'RequestToken' in query_params:
                token = query_params['RequestToken'][0]
                logger.info("RequestToken found in URL parameter")
                return token
            
            # Fallback: Also check common token parameter names
            token_keys = ['RequestToken', 'requestToken', 'request_token', 
                         'access_token', 'token', 'accessToken', 'auth_token', 
                         'authToken', 'api_token', 'apiToken']
            
            for key in token_keys:
                if key in query_params:
                    token = query_params[key][0]
                    logger.info(f"Token found in URL parameter: {key}")
                    return token
            
            # Also check fragment/hash
            if parsed_url.fragment:
                fragment_params = parse_qs(parsed_url.fragment)
                for key in token_keys:
                    if key in fragment_params:
                        token = fragment_params[key][0]
                        logger.info(f"Token found in URL fragment: {key}")
                        return token
            
            logger.warning(f"RequestToken not found in URL. Available parameters: {list(query_params.keys())}")
            logger.warning(f"Full URL: {url}")
            return None

        except Exception as e:
            logger.error(f"Error extracting RequestToken from URL: {str(e)}")
            return None

    def _extract_token_from_response(self, response_text: str) -> Optional[str]:
        """
        Extract AccessToken from backend callback response body.
        
        Expected format: "AccessToken Generated : <token>"
        """
        try:
            match = re.search(r"AccessToken\s+Generated\s*:\s*(\S+)", response_text)
            if match:
                token = match.group(1).strip()
                logger.info("AccessToken found in backend response body")
                return token
            logger.warning("AccessToken not found in backend response body")
            return None
        except Exception as e:
            logger.error(f"Error extracting token from backend response: {str(e)}")
            return None

    async def _debug_page_structure(self, stage: str):
        """Debug helper to capture page structure, inputs, and screenshot"""
        try:
            # Take screenshot
            screenshot_path = f"debug_{stage}_screenshot.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            # Save page HTML
            html_content = await self.page.content()
            html_path = f"debug_{stage}_page.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"📄 HTML saved: {html_path}")
            
            # Extract all input fields with their attributes
            inputs_info = await self.page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input'));
                    return inputs.map(input => ({
                        tag: input.tagName,
                        type: input.type,
                        id: input.id || null,
                        name: input.name || null,
                        placeholder: input.placeholder || null,
                        className: input.className || null,
                        value: input.value || null,
                        visible: input.offsetParent !== null,
                        attributes: Array.from(input.attributes).map(attr => ({
                            name: attr.name,
                            value: attr.value
                        }))
                    }));
                }
            """)
            
            # Log all input fields
            logger.info("=" * 80)
            logger.info(f"🔍 DEBUG: All Input Fields Found on {stage.upper()} Page:")
            logger.info("=" * 80)
            for idx, inp in enumerate(inputs_info, 1):
                logger.info(f"\nInput #{idx}:")
                logger.info(f"  Type: {inp['type']}")
                logger.info(f"  ID: {inp['id']}")
                logger.info(f"  Name: {inp['name']}")
                logger.info(f"  Placeholder: {inp['placeholder']}")
                logger.info(f"  Class: {inp['className']}")
                logger.info(f"  Visible: {inp['visible']}")
                logger.info(f"  All Attributes: {inp['attributes']}")
            
            # Save to JSON file for easy reading
            debug_path = f"debug_{stage}_inputs.json"
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(inputs_info, f, indent=2)
            logger.info(f"💾 Input fields data saved: {debug_path}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error in debug capture: {e}")

    async def _debug_find_all_inputs(self, stage: str):
        """Find all input fields when selector fails"""
        try:
            # Get all input elements
            all_inputs = await self.page.query_selector_all("input")
            logger.info(f"Found {len(all_inputs)} input elements on the page")
            
            for idx, inp in enumerate(all_inputs, 1):
                try:
                    inp_id = await inp.get_attribute("id")
                    inp_name = await inp.get_attribute("name")
                    inp_placeholder = await inp.get_attribute("placeholder")
                    inp_type = await inp.get_attribute("type")
                    inp_class = await inp.get_attribute("class")
                    
                    logger.info(f"Input #{idx}: id={inp_id}, name={inp_name}, placeholder={inp_placeholder}, type={inp_type}, class={inp_class}")
                except:
                    pass
        except Exception as e:
            logger.error(f"Error finding inputs: {e}")

    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")


async def login_and_get_token() -> Optional[str]:
    """
    Convenience function to login and get access token
    
    Returns:
        Access token string if successful, None otherwise
    """
    login_handler = FivePaisaLogin()
    try:
        token = await login_handler.login()
        return token
    finally:
        await login_handler.close()
