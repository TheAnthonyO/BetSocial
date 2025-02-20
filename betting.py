import random

class Bet:
    def __init__(self, user, team, amount, odds=2.0):
        self.user = user
        self.team = team
        self.amount = amount
        self.odds = odds
        self.result = None  # 'win' or 'lose'
        self.result_description = "Pending"

    def process_result(self, winning_team):
        """ Determines if the user won or lost the bet. """
        if self.team == winning_team:
            self.result = 'win'
            winnings = self.amount * self.odds
            self.user.update_bankroll(winnings)
            self.result_description = f"Win - {winning_team}"
        else:
            self.result = 'lose'
            self.user.update_bankroll(-self.amount)
            self.result_description = f"Loss - {winning_team}"

class BettingSystem:
    def __init__(self):
        self.bets = []

    def place_bet(self, user, team, amount, odds=2.0):
        if user.bankroll < amount:
            return None  # Indicate insufficient funds

        bet = Bet(user, team, amount, odds)
        self.bets.append(bet)
        user.update_bankroll(-amount)
        return bet

    def settle_bets(self):
        winning_team = random.choice(["Team A", "Team B"])

        for bet in self.bets:
            if bet.result is None:  # Only settle pending bets
                bet.process_result(winning_team)

        return winning_team
