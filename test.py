import random

def generate_sequence(player1_wins, player2_wins):
    total_games = player1_wins + player2_wins
    sequence = []
    count = 0
    player1_winrate = player1_wins/total_games
    while total_games > len(sequence):
        # Calculate the current ratio of player1_wins
        loss_ratio = count / (len(sequence) + 1)
        win_ratio = (count + 1) / (len(sequence) + 1)
        win_delta = win_ratio - player1_winrate
        loss_delta = player1_winrate - loss_ratio

        if win_delta == loss_delta:
            if random.choice([0, 1]):
                sequence.append(1)
                count += 1
            else:
                sequence.append(2)
        elif win_delta < loss_delta:
            sequence.append(1)
            count += 1
        else:
            sequence.append(2)
        
    return sequence

def test_generate_sequence():
    total_tests = 1000
    for _ in range(total_tests):
        player1_wins = random.randint(0, 100)
        player2_wins = random.randint(0, 100)
        sequence = generate_sequence(player1_wins, player2_wins)

        # Check if the sequence has the correct number of 1s and 2s
        count_1s = sequence.count(1)
        count_2s = sequence.count(2)

        assert count_1s == player1_wins, f"Test failed with player1_wins={player1_wins}, player2_wins={player2_wins}"
        assert count_2s == player2_wins, f"Test failed with player1_wins={player1_wins}, player2_wins={player2_wins}"

    print(f"All {total_tests} tests passed successfully!")

# Run the tests
test_generate_sequence()