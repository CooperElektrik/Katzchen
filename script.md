## Start
**Alice**: Do you have the key?
@ has_key = false
> Secret ? has_key
Narrator: You stay in the hallway.

## Secret
Narrator: You unlock the door and enter the secret room.
- [Take the treasure](Treasure) set money=100
- [Leave quietly](Hallway)

## Treasure
Narrator: You grab the treasure. You're now rich!
> Ending ? money > 50

## Hallway
Narrator: You wander away.

## Ending
Narrator: Congratulations! You reached the rich ending.