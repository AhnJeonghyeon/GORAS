# GOR project

The project aims to build a system in which proactive agents interact with each other to decide what goals/tasks they take based on what they sense from the environments and other agents. Through this project, we should be able to tell what strategy of distributing tasks/goals would be better for obtaining higher profit to them. Moreover, all interactions should be monitored and analyzed to tell what are the conditions or constraints that they would have to proceed their interactions.

 Requirements

* Starcraft II
* Python3
* Python3 libraries (blah)

# How to use

To run a simulation,
```
# launch option creates SC2 instance, if an instance is already running, skip this option
# log option logs all activities during the simulation
$ python3 core.py --launch
```

# For developers

## Commits

Since we are a small number of group, any changes you make should first go to a branch `git checkout -b YOUR_BRANCH` from `master`. After you committed all updates/changes and tested them, you can make a `pull request` to `master`. Someone will review and merge it. When project becomes larger we can consider having `develop` branch which takes all changes/updates and have `master` get only stable version of the project.



