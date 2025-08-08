from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
import subprocess
from subjective_abstract_data_source_package import SubjectiveDataSource
from brainboost_data_source_logger_package.BBLogger import BBLogger


class SubjectiveBinanceP2POffersDataSource(SubjectiveDataSource):
    def __init__(self, name=None, session=None, dependency_data_sources=[], subscribers=None, params=None):
        super().__init__(name=name, session=session, dependency_data_sources=dependency_data_sources,
                         subscribers=subscribers, params=params)
        self._total_items = 0
        self._processed_items = 0
        self._total_processing_time = 0.0
        self._fetch_completed = False

    def fetch(self):
        start_time = time.time()
        trading_pair = self.params.get('trading_pair', 'BTC_USDT')
        target_directory = self.params.get('target_directory', '')
        BBLogger.log(f"Starting Binance P2P fetch for trading pair '{trading_pair}' into '{target_directory}'.")

        if not os.path.exists(target_directory):
            os.makedirs(target_directory)
            BBLogger.log(f"Created directory {target_directory}")

        # Fetch P2P offers
        offers = self._fetch_p2p_offers(trading_pair)
        self._total_items = len(offers)
        BBLogger.log(f"Found {self._total_items} P2P offers.")

        for offer in offers:
            step_start = time.time()
            BBLogger.log(f"Processing offer: {offer}")
            # Process each offer (save to file, database, etc.)
            self._process_offer(offer, target_directory)
            
            elapsed = time.time() - step_start
            self._total_processing_time += elapsed
            self._processed_items += 1
            if self.progress_callback:
                est_time = self.estimated_remaining_time()
                self.progress_callback(self.get_name(), self.get_total_to_process(), self.get_total_processed(), est_time)
        
        self._fetch_completed = True
        BBLogger.log("Binance P2P fetch process completed.")

    def _fetch_p2p_offers(self, trading_pair):
        """Fetch P2P offers from Binance"""
        # Configure Selenium options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        offers_data = []
        
        try:
            # Navigate to Binance P2P
            url = f"https://p2p.binance.com/en/trade/{trading_pair}"
            driver.get(url)
            
            # Wait for the page to load
            time.sleep(5)  # Adjust as necessary

            # Example: Extract offer elements
            offers = driver.find_elements(By.CLASS_NAME, "css-1sv7ku3")  # Update with actual class names
            
            for offer in offers:
                try:
                    seller = offer.find_element(By.CLASS_NAME, "css-1gw9lzm").text  # Update class name
                    price = offer.find_element(By.CLASS_NAME, "css-1uvkrz3").text  # Update class name
                    min_amt = offer.find_element(By.CLASS_NAME, "css-1w0m5x8").text  # Update class name
                    max_amt = offer.find_element(By.CLASS_NAME, "css-1w0m5x8").text  # Update class name
                    payment_methods = [pm.text for pm in offer.find_elements(By.CLASS_NAME, "css-1pm6sv3")]  # Update class name
                    
                    offer_data = {
                        "seller": seller,
                        "price": price,
                        "min_amount": min_amt,
                        "max_amount": max_amt,
                        "payment_methods": payment_methods,
                        "trading_pair": trading_pair
                    }
                    offers_data.append(offer_data)
                    BBLogger.log(f"Extracted offer: {offer_data}")
                except Exception as e:
                    BBLogger.log(f"Error extracting offer details: {e}", level="error")
            
        except Exception as e:
            BBLogger.log(f"Error navigating to Binance P2P: {e}", level="error")
        finally:
            driver.quit()

        return offers_data

    def _process_offer(self, offer, target_directory):
        """Process and save offer data"""
        # Save offer to a file or process as needed
        filename = f"binance_p2p_offer_{offer.get('seller', 'unknown')}_{int(time.time())}.txt"
        filepath = os.path.join(target_directory, filename)
        
        try:
            with open(filepath, 'w') as f:
                f.write(str(offer))
            BBLogger.log(f"Saved offer to {filepath}")
        except Exception as e:
            BBLogger.log(f"Error saving offer to file: {e}", level="error")

    def get_icon(self):
        """Return SVG icon content, preferring a local icon.svg in the plugin folder."""
        import os
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.svg')
        try:
            if os.path.exists(icon_path):
                with open(icon_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        return '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><circle cx="10" cy="10" r="10" fill="#F3BA2F"/></svg>'

    def get_connection_data(self):
        return {
            "connection_type": "Binance_P2P",
            "fields": ["trading_pair", "target_directory"]
        }


