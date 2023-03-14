class Action:
    def __init__(self, player_num, phase, value):
        self.player_num = int(player_num)
        self.phase = phase
        self.value = value
        self.partner_num = (self.player_num + 2) % 4

    def __str__(self):
        return f"{self.player_num} {self.phase} {self.value}"

    def __repr__(self):
        return f"{self.player_num} {self.phase} {self.value}"
