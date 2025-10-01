## Start
*Knock knock.*

Naturally, one would follow those up with a "who's there," and the other person would state their name and reason for their arrival. If it was a relative or a loved one, one would welcome them in right away. If not, perhaps only a short conversation would suffice. 

**Visitor**: Hello? Is anybody home?

*Knock, knock, knock.*

This time, it is a little more insistent. The door creaks slightly, as if urging one to respond. 

One could just leave them standing there, of course. There would be no consequence. But what if it is someone who needs help? What if it is someone who just wants to share a joke, or a memory, or even just the weather? This world feels a little smaller when one opens the door, even just a tiny bit.

- [Open the door and greet them](AnswerDoor) set answered=True
- [Stay perfectly silent and wait](StaySilent) set answered=False

## AnswerDoor
```char
show alice happy.png 0.2 0.8 1.0
move alice 0.5 0.8 1.5
```
```transition
fade_out 1.0 (0,0,0,255)
fade_in 2.0 (255,255,255,128)
```
You grasp the handle and pull the heavy door inward.
A figure stands there, obscured slightly by the weak porch light. 
**Visitor**: Oh, good. I thought no one was home. I just needed to borrow a cup of sugar.
You lend them the sugar. The exchange is brief and pleasant.
> End

## StaySilent
In the end, one stayed silent, letting the moment stretch until it snaps, leaving only the sound of footsteps fading away.
The moment passed, and the house feels strangely heavy and empty.
> End

## End
The story concludes.