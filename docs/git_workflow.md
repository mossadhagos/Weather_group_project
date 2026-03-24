# Branching Strategy (GitHub Standard Flow)
---

## 1.Always start clean:

- git checkout  main (from main branch)
- git pull origin main 
---

## 2.Create your own branch:(feature branch)


- git checkout -b branch name(feature/extract(branch name/task name))
---

## 3.Check 
- git branch (to check current branch: if main or feature)

  *Note: If still on the main branch; Go back to No.1 and double check*

---


## 4.Now on your branch 
- git add . or git add file name -> git add -p file name (this is to track the file)
- git commit -m "add description validation"

### Description validation format :
- chore: for data file commit messages 
- feat: for scripts( e.g, .py or notebook)
- documents: for text files 

- git push origin branch name/task:(feature/extract)

---

## 5.After approval the team;

### Option A:Github 
- 1.Open GitHub 

- 2.Create a Pull request:
- base: main 
- compare: feature- login 

- 3.Team Reviews(When the developer is done with a particular task)

- 4.Click Merge 

 
### Option B:Locally in the terminal(Only if the team approves)
- git checkout(check-in) main
- git pull main 
- git merge my branch 
- git push origin main


- Now team can pull, review , test and comment 

*Work(Your own branch) → Commit((Your own branch) → Push(Own branch)) → Open Pull Request → Review → Merge(Main/General repo)*

*Note: Commit standards must be followed to avoid so much merge conflicts in the group*
