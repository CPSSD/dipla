# Dipla - Team Guidelines / Contribution Guide

Here are a collection of rules/guidelines being used internally by the core Dipla Team. It is **advised** that you follow these if you wish to contribute as they will _greatly_ speed up the entire process.

## Team Communication/Workload Rules

* If one is stuck on their task (or feels as if their task is too big), they **should not be afraid to openly mention it to the team**. This will prevent the team getting held back by a single person.

* If one is not pulling their weight, the team should **_politely_ ask them to do so** (and try to help them if necessary). This encourages honesty within the team. This should not be taken personally; it is for the benefit of the project.

* If one continues to show a lack of effort or output, further action should be taken to prevent the rest of the team from being negatively affected as a result. **Continuous slackers should not be protected**.

## Refactoring Guidelines

* The team should be **encouraged to follow the Boy Scout Rule** in small doses. If you see a variable or function name that could be made more descriptive, feel free to tweak it. These small tweaks will make a difference over time and benefit the codebase.

 * However, if the change is a little bit larger, you should **speak with the original author** to see if the change is okay. Communication is important to prevent this from causing issues.

* **Unit tests (and integration tests too if necessary) should be very desirable**, however they are not mandatory if they do not fit one’s approach to programming.

## Standup Rules

* Standups should last **less than 8 minutes** (2 minutes per person). Extra discussion time is fine afterwards.

* Should not be allowed to sit down at standups (to prevent distraction).

* Aim to have at **~2 standups per week**. Aim to organise them when team communication is _truly_ necessary.

## Scrum Master Rules

* Scrum master should briefly write down notes from the standups. These should be **collated together in some sort of document**. This is quite like the SCRUM Logs we're used to, but broader.

## Waffle Columns

| Column         | Description                              |
| :------------- | :--------------------------------------- |
| Backlog        | This is the Product Backlog              |
| Ready          | This is the Sprint Backlog               |
| In Progress    | Tasks currently being worked on          |
| In Review      | Tasks with an open pull request          |
| Complete       | Tasks which have been merged into master |

## Waffle Usage Rules

* No more than **2 tasks per person** can be "In Progress" at once. This will ensure each task gets completed.

* If too many tickets are "In Review", the team should **make an effort to review** them and clear the bottleneck.

## Waffle Task Rules

* This section is currently being decided.

## Code Style

* This section depends on the languages/technologies being used. This can be written **after a design document has been prepared**.

## Git Guidelines

* Branches are named like so:

 * `assignee_first_initial/issue_name#issue_number`

 * For multiple assignees the initals can be hyphenated.
   * `c/atom_support#43`
   * `c-r/atom_support#43`

* Commit messages should be written in “tenseless” format.
   * `git commit -m “Fix compilation error xyz in example.cpp”`
   * `git commit -m "Create CONTRIBUTING.md in project root"`

* Commit messages should clearly describe the small feature they address.

* Master must _always_ compile and pass _all_ of the tests. Any pull requests with merge conflicts or failing tests **should not be accepted**.

* _Extensive_ code review must take place on each pull request. At **least 2 members must give the “go ahead”** on a branch before it can be merged. This will ensure that less silly mistakes get into master.

* Be **harsh and pedantic** with your code reviews... Even if the author has only slightly violated the style guide.

## Code Documentation

* Any interfaces being used by the public **should be documented appropriately**. This only applies to public classes, public methods and public functions. Code with non-public visibility should not need as much, _if any_, special documentation.

* Internal team code **does not require** strict documentation. This is because **documentation is known to rot** if not continuously maintained  while the code changes. However, a file can be briefly documented at the top to give a quick overview of its purpose.
