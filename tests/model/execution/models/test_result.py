# Case Conductor is a Test Case Management system.
# Copyright (C) 2011-2012 Mozilla
#
# This file is part of Case Conductor.
#
# Case Conductor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Case Conductor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Case Conductor.  If not, see <http://www.gnu.org/licenses/>.
"""
Tests for Result model.

"""
from datetime import datetime

from django.test import TestCase

from mock import patch

from .... import factories as F
from ....utils import refresh



class ResultTest(TestCase):
    """Tests for Result."""
    def test_unicode(self):
        env = F.EnvironmentFactory.create_full_set(
            {"OS": ["OS X"], "Language": ["English"]})[0]

        r = F.ResultFactory(
            status="started",
            runcaseversion__run__name="FF10",
            runcaseversion__caseversion__name="Open URL",
            tester__username="tester",
            environment=env,
            )

        self.assertEqual(
            unicode(r),
            u"Case 'Open URL' included in run 'FF10', "
            "run by tester in English, OS X: started")


    def test_bug_urls(self):
        """Result.bug_urls aggregates bug urls from step results, sans dupes."""
        r = F.ResultFactory()
        F.StepResultFactory.create(result=r)
        F.StepResultFactory.create(
            result=r, bug_url="http://www.example.com/bug1")
        F.StepResultFactory.create(
            result=r, bug_url="http://www.example.com/bug1")
        F.StepResultFactory.create(
            result=r, bug_url="http://www.example.com/bug2")

        self.assertEqual(
            r.bug_urls(),
            set(["http://www.example.com/bug1", "http://www.example.com/bug2"])
            )


    def test_start(self):
        """Start method marks status started and sets started timestamp."""
        r = F.ResultFactory.create()

        with patch("cc.model.execution.models.utcnow") as mock_utcnow:
            mock_utcnow.return_value = datetime(2012, 2, 3)
            r.start()

        r = refresh(r)
        self.assertEqual(r.status, "started")
        self.assertEqual(r.started, datetime(2012, 2, 3))


    def test_start_sets_modified_user(self):
        """Start method can set modified-by user."""
        r = F.ResultFactory.create()
        u = F.UserFactory.create()

        r.start(user=u)

        self.assertEqual(refresh(r).modified_by, u)


    def test_finishsucceed(self):
        """Finishsucceed marks status passed and sets completed timestamp."""
        r = F.ResultFactory.create(status="started")

        with patch("cc.model.execution.models.utcnow") as mock_utcnow:
            mock_utcnow.return_value = datetime(2012, 2, 3)
            r.finishsucceed()

        r = refresh(r)
        self.assertEqual(r.status, "passed")
        self.assertEqual(r.completed, datetime(2012, 2, 3))


    def test_finishsucceed_sets_modified_user(self):
        """Finishsucceed method can set modified-by user."""
        r = F.ResultFactory.create(status="started")
        u = F.UserFactory.create()

        r.finishsucceed(user=u)

        self.assertEqual(refresh(r).modified_by, u)


    def test_finishinvalidate(self):
        """Finishinvalidate sets status invalidated and completed timestamp."""
        r = F.ResultFactory.create(status="started")

        with patch("cc.model.execution.models.utcnow") as mock_utcnow:
            mock_utcnow.return_value = datetime(2012, 2, 3)
            r.finishinvalidate()

        r = refresh(r)
        self.assertEqual(r.status, "invalidated")
        self.assertEqual(r.completed, datetime(2012, 2, 3))


    def test_finishinvalidate_sets_modified_user(self):
        """Finishinvalidate method can set modified-by user."""
        r = F.ResultFactory.create(status="started")
        u = F.UserFactory.create()

        r.finishinvalidate(user=u)

        self.assertEqual(refresh(r).modified_by, u)


    def test_finishinvalidate_with_comment(self):
        """Finishinvalidate method can include comment."""
        r = F.ResultFactory.create(status="started")

        r.finishinvalidate(comment="and this is why")

        self.assertEqual(refresh(r).comment, "and this is why")


    def test_finishfail(self):
        """Finishfail sets status failed and completed timestamp."""
        r = F.ResultFactory.create(status="started")

        with patch("cc.model.execution.models.utcnow") as mock_utcnow:
            mock_utcnow.return_value = datetime(2012, 2, 3)
            r.finishfail()

        r = refresh(r)
        self.assertEqual(r.status, "failed")
        self.assertEqual(r.completed, datetime(2012, 2, 3))


    def test_finishfail_sets_modified_user(self):
        """Finishfail method can set modified-by user."""
        r = F.ResultFactory.create(status="started")
        u = F.UserFactory.create()

        r.finishfail(user=u)

        self.assertEqual(refresh(r).modified_by, u)


    def test_finishfail_with_comment(self):
        """Finishfail method can include comment."""
        r = F.ResultFactory.create(status="started")

        r.finishfail(comment="and this is why")

        self.assertEqual(refresh(r).comment, "and this is why")


    def test_finishfail_with_stepnumber(self):
        """Finishfail method can mark particular failed step."""
        step = F.CaseStepFactory.create(number=1)
        r = F.ResultFactory.create(
            status="started", runcaseversion__caseversion=step.caseversion)

        r.finishfail(stepnumber="1")

        sr = r.stepresults.get()
        self.assertEqual(sr.step, step)
        self.assertEqual(sr.status, "failed")


    def test_finishfail_with_stepnumber_and_existing_stepresult(self):
        """Finishfail method can update existing step result."""
        step = F.CaseStepFactory.create(number=1)
        r = F.ResultFactory.create(
            status="started", runcaseversion__caseversion=step.caseversion)
        sr = F.StepResultFactory.create(result=r, step=step, status="passed")

        r.finishfail(stepnumber="1")

        updated = r.stepresults.get()
        self.assertEqual(updated, sr)
        self.assertEqual(updated.step, step)
        self.assertEqual(updated.status, "failed")


    def test_finishfail_with_stepnumber_and_bug(self):
        """Finishfail method can include bug with failed step."""
        step = F.CaseStepFactory.create(number=1)
        r = F.ResultFactory.create(
            status="started", runcaseversion__caseversion=step.caseversion)

        r.finishfail(stepnumber="1", bug="http://www.example.com/")

        sr = r.stepresults.get()
        self.assertEqual(sr.bug_url, "http://www.example.com/")


    def test_finishfail_bad_stepnumber_ignored(self):
        """Finishfail method ignores bad stepnumber."""
        step = F.CaseStepFactory.create(number=1)
        r = F.ResultFactory.create(
            status="started", runcaseversion__caseversion=step.caseversion)

        r.finishfail(stepnumber="2")

        self.assertEqual(r.stepresults.count(), 0)


    def test_restart(self):
        """Restart method marks status started and sets started timestamp."""
        r = F.ResultFactory.create(
            status="passed", started=datetime(2011, 12, 1))

        with patch("cc.model.execution.models.utcnow") as mock_utcnow:
            mock_utcnow.return_value = datetime(2012, 2, 3)
            r.restart()

        r = refresh(r)
        self.assertEqual(r.status, "started")
        self.assertEqual(r.started, datetime(2012, 2, 3))


    def test_restart_sets_modified_user(self):
        """Restart method can set modified-by user."""
        r = F.ResultFactory.create()
        u = F.UserFactory.create()

        r.restart(user=u)

        self.assertEqual(refresh(r).modified_by, u)


    def test_restart_clears_completed_timestamp(self):
        """Restart method clears completed timestamp."""
        r = F.ResultFactory.create(completed=datetime(2011, 12, 1))

        r.restart()

        self.assertEqual(refresh(r).completed, None)


    def test_restart_clears_comment(self):
        """Restart method clears comment."""
        r = F.ResultFactory.create(
            status="invalidated", comment="it ain't valid")

        r.restart()

        self.assertEqual(refresh(r).comment, "")


    def test_restart_clears_stepresults(self):
        """Restart method clears any step results."""
        sr = F.StepResultFactory.create(
            status="failed", result__status="failed")

        sr.result.restart()

        r = refresh(sr.result)
        self.assertEqual(r.status, "started")
        self.assertEqual(r.stepresults.count(), 0)
