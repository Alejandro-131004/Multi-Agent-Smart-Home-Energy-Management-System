# agent.py

class EnergyAgent:
    def __init__(self, name, password, environment):
        self.name = name
        self.password = password
        self.environment = environment
        self.current_price = None  # Initialize the current price variable

    def start(self):
        print(f"{self.name} agent started.")

    def stop(self):
        print(f"{self.name} agent stopped.")

    def update_price(self):
        """Update the current price from the environment."""
        self.current_price = self.environment.get_price_for_current_hour()

    def act_on_price(self):
        """Take action based on the current energy price."""
        if self.current_price is not None:
            print(f"{self.name} received energy price: {self.current_price}")

            # Example decision-making based on price
            if self.current_price < 0.15:  # If the price is low, suggest using more energy
                print(f"{self.name}: It's a good time to consume more energy.")
            elif self.current_price > 0.30:  # If the price is high, suggest conserving energy
                print(f"{self.name}: It's a good time to conserve energy.")
        else:
            print(f"{self.name} could not retrieve the current price.")

