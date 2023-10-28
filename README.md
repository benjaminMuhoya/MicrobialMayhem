# MicrobialMayhem
May the best microbe win!


```
import random

class Microbe:
    def __init__(self, name, gene_content, colony_size):
        self.name = name
        self.gene_content = gene_content  # Dictionary with gene name and its presence (1/0)
        self.colony_size = colony_size
        self.strength = self.calculate_strength()
        
    def calculate_strength(self):
        # Here, we simply sum up the gene contents and add the colony size for simplicity.
        # You can use more sophisticated models/formulas to determine the strength.
        return sum(self.gene_content.values()) + self.colony_size

def battle(microbe1, microbe2):
    if microbe1.strength > microbe2.strength:
        return microbe1
    elif microbe2.strength > microbe1.strength:
        return microbe2
    else:
        return random.choice([microbe1, microbe2])  # In case of a tie, choose randomly

def main():
    # Sample microbes
    e_coli = Microbe("E. coli", {"geneA": 1, "geneB": 0, "geneC": 1}, 1000)
    bacillus = Microbe("Bacillus", {"geneA": 0, "geneB": 1, "geneC": 0}, 800)
    
    print("Choose two microbes to battle!")
    print("1. E. coli")
    print("2. Bacillus")
    
    choice1 = int(input("Choose the first microbe (1/2): "))
    choice2 = int(input("Choose the second microbe (1/2): "))
    
    if choice1 == 1:
        m1 = e_coli
    else:
        m1 = bacillus
        
    if choice2 == 1:
        m2 = e_coli
    else:
        m2 = bacillus
        
    winner = battle(m1, m2)
    print(f"The winner is {winner.name}!")

if __name__ == "__main__":
    main()

```
