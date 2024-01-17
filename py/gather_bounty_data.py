from functools import total_ordering
from github import Github
from github import Auth
from os import environ

COOL_REPO = "Mudlet/Mudlet"
COOL_EVENTS = ["labeled"]
COOL_LABELS = ["bounty-paid", "bounty-20", "bounty-30", "bounty-50", "bounty-80", "bounty-100", "bounty-120", "bounty-200" ]

try:
    GITHUB_ACCESS_TOKEN = environ["GITHUB_ACCESS_TOKEN"]
except KeyError:
    raise(ValueError("Token not available!"))


@total_ordering
class Bounty():
  def __init__(self, number, reward = 0, title = ""):
    self.number = number
    self.reward = reward
    if title == "":
      self.title = "Title unknown"
    else:
      self.title = title
      
    self.status = "plan"
    self.url = f"https://github.com/Mudlet/Mudlet/issues/{self.number}"
    self.start_date = ""
    self.end_date = ""

  def publish(self, start_date, reward):
    self.start_date = start_date
    self.reward = reward
    self.status = "open"

  def close(self, end_date, status = "abort"):
    self.end_date = end_date
    self.status = status

  def pay(self, end_date):
    self.end_date = end_date
    self.status = "paid"

  def __str__(self):
    link_string = f'=HYPERLINK("{self.url}";"{self.title}")'
    return "\t".join((
      str(self.number), 
      link_string, 
      self.status, 
      str(self.reward), 
      str(self.start_date), 
      str(self.end_date)))

  def __repr__(self):
    return "Bounty(%r, %r, %r)" % (self.number, self.reward, self.title)

  def __eq__(self, other): 
    result = (self.number == other.number) and \
      (self.start_date == other.start_date)
    return result
    
  def __lt__(self, other): 
    result = (self.number < other.number) and \
      (self.start_date < other.start_date)
    return result

  def __hash__(self):
    return hash((self.number, self.start_date))


def is_no_pull_request(issue):
    return issue.pull_request is None


def gather_cool_issues(repo):
    cool_issues = set()
    for label in COOL_LABELS:
        cool_issues.update(repo.get_issues(
            labels = [label], state = "all"))

    cool_issues = set(c for c in cool_issues if is_no_pull_request(c))
    return cool_issues


def parse_issue(issue):
    bounty = Bounty(issue.number, title = issue.title)
    bounties = {bounty}
    for event in [e for e in issue.get_timeline() if e.event in COOL_EVENTS]:
        label_name = event.raw_data['label']['name']
        if label_name not in COOL_LABELS:
            continue

        if label_name == "bounty-paid":
            bounty.pay(end_date = event.created_at)
            continue

        # Now the label must either be "bounty-20", or "bounty-30", etc.
        reward = label_name.split("-")[1]
        if bounty.status == "open":
            # This bounty was already published before, now changed to a different reward.
            # Then we will close the original bounty, and create a new bounty with the new reward.
            bounty.close(end_date = event.created_at, status = "rise")
            bounty = Bounty(issue.number, title = issue.title)
            bounties.add(bounty)

        bounty.publish(start_date = event.created_at, reward = reward)

    return bounties


def main():
    auth = Auth.Token(GITHUB_ACCESS_TOKEN)
    github = Github(auth=auth)
    repo = github.get_repo(COOL_REPO)

    cool_issues = gather_cool_issues(repo)
    bounties = set()
    for issue in cool_issues:
        bounties.update(parse_issue(issue))

    with open("bounty.txt", "w") as out_file:
        out_file.write("\n".join(str(line) for line in sorted(bounties)))
    

if __name__ == "__main__":
    main()