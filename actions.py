"""Available actions of the agent."""

import numpy as np


# def abs_diff_l_than(p1, p2, val):
#     return np.all(np.abs(p1 - p2) < val)


# def abs_diff_leq_than(p1, p2, val):
#     return np.all(np.abs(p1 - p2) <= val)


# def abs_diff_g_than(p1, p2, val):
#     return np.all(np.abs(p1 - p2) > val)


# def abs_diff_geq_than(p1, p2, val):
#     return np.all(np.abs(p1 - p2) >= val)


# def abs_diff_eq_to(p1, p2, val):
#     return np.all(np.abs(p1 - p2) == val)

def abs_diff_l_than(p1, p2, val):
    return np.all(np.sum(np.abs(p1 - p2)) < val)


def abs_diff_leq_than(p1, p2, val):
    return np.all(np.sum(np.abs(p1 - p2)) <= val)


def abs_diff_g_than(p1, p2, val):
    return np.all(np.sum(np.abs(p1 - p2)) > val)


def abs_diff_geq_than(p1, p2, val):
    return np.all(np.sum(np.abs(p1 - p2)) >= val)


def abs_diff_eq_to(p1, p2, val):
    return np.all(np.sum(np.abs(p1 - p2)) == val)


class Action:
    def __init__(self, type, name, color, marker):
        self.type = type
        self.name = name
        self.color = color
        self.marker = marker

    def preconditions(self, env):
        return True

    def effects(self, env, agent):
        return 0


class Eat(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'eat', 'b', 'o')

    def preconditions(self, env):
        """Food in jaws."""
        return abs_diff_l_than(env.food, env.mouth, 1)

    def effects(self, env, agent):
        """Hunger reduces; positive reinforcement."""
        # env.reset()
        # env.compute_population_codes()
        agent.hunger = 0
        return 1


class GraspJaws(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'grasp_jaws', 'g', 's')

    def preconditions(self, env):
        """Food close to jaws."""
        return (abs_diff_g_than(env.food, env.mouth, 1) &
                abs_diff_leq_than(env.food, env.mouth, 5))

    def effects(self, env, agent):
        """Mouth moves to food."""
        env.mouth = env.food[:]
        env.compute_population_codes()
        return 0


class BringToMouth(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'bring_to_mouth', 'r', 'x')

    def preconditions(self, env):
        """Food grasped by paw, but not close to mouth."""
        return (abs_diff_eq_to(env.food, env.paw, 0) &
                abs_diff_g_than(env.mouth, env.food, 5))

    def effects(self, env, agent):
        """Bring paw close to mouth with food still grasped by paw.

        This makes the Grasp-Jaws schema executable without putting
        the food inside the mouth yet
        """
        env.paw = env.mouth + [5, 0]
        env.food = env.paw[:]
        env.compute_population_codes()
        return 0


class GraspPaw(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'grasp_paw', 'c', '.')
        self.lesion = lesion

    def preconditions(self, env):
        """Paw close to food.

        If the max distance for executability is changed from 5 to 2
        then the action ReachFood will become necessary.
        """
        return (abs_diff_g_than(env.paw, env.food, 0) &
                abs_diff_leq_than(env.paw, env.food, 5))

    def effects(self, env, agent):
        """Paw grasps food."""
        if not self.lesion:
            env.paw = env.food[:]
        else:
            env.paw = env.food + [0, 5]
            # In the paper a random number in range [-10, 2] is added
            # Slightly changed, as it seemed to work better with the
            # network tested, but other limits work too
            env.food[0] = min(30, env.food[0] + np.random.randint(low=-8,
                                                                  high=3))
            if env.food[0] < 0:
                env.food[0] = 0
            if env.food[1] == env.tube[1] and env.food[0] < env.tube[0]:
                env.food[1] = 0
        env.compute_population_codes()
        return 0


class ReachFood(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'reach_food', 'm', '|')

    def preconditions(self, env):
        """Food in tube and paw aligned with or within tube or food on floor
        but not close to paw
        """
        # SOS -- Maybe wrong in the paper
        return ((abs_diff_geq_than(env.food, env.paw, 5) &
                (env.food[1] == 0)) |
                (((env.food[1] == env.tube[1]) &
                 abs_diff_l_than(env.paw, env.tube, 5))))

    def effects(self, env, agent):
        """Paw is moved close enough to the food to grasp it"""
        env.paw = env.food + [0, 1]
        env.compute_population_codes()
        return 0


class ReachTube(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'reach_tube', 'y', '*')

    def preconditions(self, env):
        """Paw not near tube"""
        # SOS first condition
        return ((env.paw[0] < env.tube[0]) | (env.paw[1] != (env.tube[1] + 1)))
                # (env.paw != env.tube + [3, 1]).all())  # Last cond not in paper

    def effects(self, env, agent):
        """Move paw inside the tube, near the end
        If the food is currently already grasped, it moves with the paw
        """
        temp_paw = env.paw[:]
        env.paw = env.tube + [3, 1]
        if np.all(env.food == temp_paw):
            env.food = env.paw[:]
        env.compute_population_codes()
        return 0


class Rake(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'rake', 'darkgrey', 'D')

    def preconditions(self, env):
        """Paw at a position both beyond and higher than the food."""
        return ((abs_diff_g_than(env.paw, env.food, 0) &
                 abs_diff_leq_than(env.paw, env.food, 5)) &
                (env.paw[0] >= env.food[0]) & (env.paw[1] > env.food[1]) &
                (env.food[0] > 1))

    def effects(self, env, agent):
        """If food is in the tube, knock it to the ground.

        If it is already on the ground, rake it closer to the body if...
        """
        if env.food[1] > 0:
            env.food[0] = env.tube[0] - 1
            env.food[1] = 0
        else:
            env.food = np.asarray([1, 0])
        env.paw = env.food + [1, 3]
        env.compute_population_codes()
        return 0


class LowerNeck(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'lower_neck', 'rosybrown', '1')

    def preconditions(self, env):
        """Neck above lowest position."""
        return env.mouth[1] > 3

    def effects(self, env, agent):
        """Bring neck to lowest position."""
        env.mouth[1] = 3
        if np.all(env.food == env.mouth):
            env.food = env.mouth[:]
        env.compute_population_codes()
        return 0


class RaiseNeck(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'relevant', 'raise_neck', 'darksalmon', '2')

    def preconditions(self, env):
        """Neck below highest position."""
        return env.mouth[1] < env.v_max

    def effects(self, env, agent):
        """Bring neck to highest position."""
        env.mouth[1] = env.v_max
        if np.all(env.food == env.mouth):
            env.food = env.mouth[:]
        env.compute_population_codes()
        return 0


class IrrelevantAction(Action):
    def __init__(self, lesion=False):
        Action.__init__(self, 'irrelevant', 'irrelevant_action', 'brown', '')
