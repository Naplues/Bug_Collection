项目配置：
   /Version_Info/Project_Name.csv 记录项目的版本信息，包括版本对应的分支信息、版本号、版本对应的commit号、版本发布时间
   /Bug_Reports/Project_Name/bugId.csv 记录项目的所有缺陷报告信息，包括缺陷编号(用于缺陷报告同commit匹配)，缺陷类型(Bug)，缺陷当前状态等
   /Code_Repository/ 记录项目的完整代码仓库(从代码仓库git clone获得)
   /Bug_Collection_Results/ 记录缺陷收集的结果

项目依赖：
   unidiff: https://pypi.org/project/unidiff/

运行方法：
   python extract_git.py
   python get_version_bug.py

运行结果：
   extract_git.py输出结果：bug_commits_lines_info.csv，描述发生变更的commit号，发生变更的文件路径，发生变更的代码行号，发生变更的代码git blame追溯到的commit号
   get_version_bug.py输出结果：(1) bug_commits_lines_versions_info.csv，在bug_commits_lines_info.csv的结果基础上实现缺陷影响版本的标注
                              (2) bug_commits_lines_versions_lines_info.csv，在bug_commits_lines_versions_info.csv的基础上，定位缺陷代码在特定版本中对应的行