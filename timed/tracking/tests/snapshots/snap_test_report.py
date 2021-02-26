# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_report_notify_rendering 1"
] = """
Some of your reports have been changed.

Reviewer: Test User


Date: 06/27/1970
Duration: 2:30 (h:mm)

Comment: some other comment

* Task
  [old] Dickerson, George and White > Horizontal analyzing product > and Sons
  [new] Dickerson, George and White > Horizontal analyzing product > Group

---

Date: 11/02/1975
Duration: 0:15 (h:mm)
Task: Dickerson, George and White > Horizontal analyzing product > Group
Comment: some other comment

* Not_Billable
  [old] True
  [new] False

---

Date: 05/14/1976
Duration: 3:15 (h:mm)



* Task
  [old] Dickerson, George and White > Horizontal analyzing product > Ltd
  [new] Dickerson, George and White > Horizontal analyzing product > Group

* Comment
  [old] foo
  [new] some other comment

---

Date: 04/20/2005
Duration: 1:00 (h:mm)
Task: Dickerson, George and White > Horizontal analyzing product > Group


* Comment
  [old] original comment
  [new] some other comment

---
"""
