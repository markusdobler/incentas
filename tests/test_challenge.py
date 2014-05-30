from .common_test_base import *

from app import models
from datetime import datetime, timedelta

class ChallengeTestCase(TrackerTestCase):

    def _new_user_and_challenge(self, user=None, username="user", **challenge_args):
        if user is None:
            user = self.create_user(username, 'password')
        args = dict(user=user, duration=timedelta(3), title="title",
                    description="description")
        args.update(challenge_args)
        ch = models.Challenge(**args)
        return user, ch


    # test business logic
    def test_create_challenge(self):
        user = self.create_user('user', 'password')
        other_user = self.create_user('user2', 'password2')
        now = datetime.now()
        ch = models.Challenge(user, timedelta(3), "title", "description",
                              target_value=10, now=now)

        assert len(user.challenges.all()) == 1
        assert len(other_user.challenges.all()) == 0


    def test_challenge_progess_to_success(self):
        """ While the challenge is running and the target value has not been
        reached, award zero points.  When the challenge has been completed successfully,
        award points depending on points_success and the overachievment ratio.
        Do this even if the challenge is overdue."""
        user, ch = self._new_user_and_challenge(target_value=100, duration=timedelta(1),
                                                points_success=5, points_fail=-10)

        def metrics(ch, now=None):
            return (
                ch.calc_points(now),
                ch.is_overdue(now),
                ch.is_success(),
                ch.is_fail(now),
                ch.clipped_percentage_value(),
                ch.clipped_percentage_time(now),
            )
        halftime = ch.start + timedelta(.5)
        p1 = ch._overachievement_ratio_to_points(1)
        p4 = ch._overachievement_ratio_to_points(4)
        overdue_time = datetime.now() + timedelta(2)

        assert metrics(ch) == (0, False, False, False, 0, 0)
        assert metrics(ch, halftime) == (0, False, False, False, 0, 0.5)
        ch.add_progress(10)
        assert metrics(ch) == (0, False, False, False, 0.1, 0)
        ch.add_progress(89)
        assert metrics(ch) == (0, False, False, False, 0.99, 0)
        ch.add_progress(1)
        assert metrics(ch) == (p1, False, True, False, 1, 0)
        ch.add_progress(300)
        assert metrics(ch) == (p4, False, True, False, 1, 0)
        assert metrics(ch, overdue_time) == (p4, True, True, False, 1, 1)


    def test_challenge_progress_to_fail(self):
        """ If the challenge is overdue, return points_fail -- even if the
        challenge has nearly been completed"""
        user, ch = self._new_user_and_challenge(target_value=100, duration=timedelta(1),
                                                points_success=5, points_fail=-10)

        def metrics(ch, now=None):
            return (
                ch.calc_points(now),
                ch.is_overdue(now),
                ch.is_success(),
                ch.is_fail(now),
                ch.clipped_percentage_value(),
                ch.clipped_percentage_time(now),
            )
        halftime = ch.start + timedelta(.5)
        overdue_time = ch.start + timedelta(2)

        assert metrics(ch) == (0, False, False, False, 0, 0)
        ch.add_progress(99)
        assert metrics(ch) == (0, False, False, False, .99, 0)
        assert metrics(ch, halftime) == (0, False, False, False, .99, .5)
        assert metrics(ch, overdue_time) == (-10, True, False, True, .99, 1)


    def test_points_from_multiple_challenges(self):
        """ The points from all successful and failed challenges of a user are added correctly.
        Challenges from other users aren't included in the calculation."""
        user, ch1 = self._new_user_and_challenge(target_value=100, duration=timedelta(1),
                                                 points_success=10, points_fail=-1)
        _, ch2 = self._new_user_and_challenge(user=user, target_value=100, duration=timedelta(1),
                                              points_success=20, points_fail=-2)
        other_user, ch_other = self._new_user_and_challenge(username="other", target_value=100, duration=timedelta(1),
                                                            points_success=40, points_fail=-4)
        _, ch3 = self._new_user_and_challenge(user=user, target_value=100, duration=timedelta(1),
                                              points_success=30, points_fail=-3)

        overdue_time = datetime.now() + timedelta(2)
        p1_4 = ch1._overachievement_ratio_to_points(4)
        p2_9 = ch2._overachievement_ratio_to_points(9)
        p1_16 = ch1._overachievement_ratio_to_points(16)

        assert user.calc_challenge_points() == 0
        ch1.add_progress(100)
        assert user.calc_challenge_points() == 10
        ch1.add_progress(300)
        assert user.calc_challenge_points() == p1_4
        ch2.add_progress(900)
        assert user.calc_challenge_points() == p1_4 + p2_9
        ch1.add_progress(1200)
        assert user.calc_challenge_points() == p1_16 + p2_9
        ch_other.add_progress(100)
        assert user.calc_challenge_points() == p1_16 + p2_9
        assert other_user.calc_challenge_points() == 40

        assert user.calc_challenge_points(overdue_time) == p1_16 + p2_9 - 3
