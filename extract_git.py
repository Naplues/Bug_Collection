import os
import re
import time
import logging
from diff_parser import parse_diff

commitWithTime = dict()
commitWithIndex = dict()

project = "accumulo"
branch_name = "master"
bug_issue_project = "ACCUMULO"
bug_pattern = r"ACCUMULO-\d+"
max_commit = ""


# 收集该branch下的所有commit 信息, 输出至Bug_Collection_Results/project_name/branch_name/commit_.txt
def git_commit_info(project, branch_name):
    global code_repository, result_root
    code_repository = "E:/Bug_Collection/Code_Repository/"
    code_repository = os.path.join(code_repository, project + "/")
    result_root = "E:/Bug_Collection/Bug_Collection_Results/"
    result_root = os.path.join(result_root, project + "/")

    if not os.path.exists(result_root):
        os.mkdir(result_root)
    result_root = os.path.join(result_root, branch_name + "/")
    if not os.path.exists(result_root):
        os.mkdir(result_root)

    os.chdir(code_repository)

    # 切换分支
    os.system("git checkout" + " " + branch_name)

    os.system("git log --pretty=format:\"%H %d\" > {}".format(os.path.join(result_root, "commit_ref.txt")))
    os.system("git log --pretty=format:\"%H %ci\" > {}".format(os.path.join(result_root, "commit_time.txt")))
    os.system("git log --pretty=format:\"%H %s\" > {}".format(os.path.join(result_root, "commit_subject.txt")))
    os.system("git log --pretty=format:\"%H %an %ae\" > {}".format(os.path.join(result_root, "commit_author.txt")))

    time.sleep(1)

    with open(os.path.join(result_root, "commit_ref.txt"), "r", encoding="utf-8") as fr:
        lines = fr.readlines()
    cnt = 0
    for line in lines:
        line = re.split("\s+", line.strip())
        commitWithTime[line[0]] = cnt
        commitWithIndex[cnt] = line[0]
        cnt += 1


# 追踪发生Modified的文件, 附加+行数 和 -行数
def git_file_change():
    tmp = "diff.txt"
    os.chdir(code_repository)
    os.system("git config diff.renameLimit 999")
    # --diff-filter=M 意味着只抽取 Modified 的文件, 不考虑Added Deleted等情况
    os.system("git log --pretty=oneline --diff-filter=M --numstat > {}".format(os.path.join(result_root, tmp)))
    print("git log --pretty=oneline --diff-filter=M --numstat > {}".format(os.path.join(result_root, tmp)))
    os.system("git config --unset diff.renameLimit")


def isSHA(val):
    return re.match("[0-9a-f]{40}", val)


def is_num(val):
    if len(val) == 40:
        return False
    flag = True
    for item in val:
        if item >= '0' and item <='9':
            continue
        else:
            flag = False
            break
    return flag


# 读jira缺陷数据
def read_bugId():
    with open(os.path.join("E:/Bug_Collection/Bug_Reports/" + bug_issue_project + "/", "bugId.csv"), "r", encoding="utf-8", errors="ignore") as fr:
        data = fr.readlines()
    for i in range(len(data)):
        data[i] = data[i].strip().split(',')[0]
    return data


# 缺陷模式匹配
def check_bug_exist(text, pattern):
    text = text.upper()
    m = re.search(bug_pattern, text)
    if not m:
        return False, ""
    else:
        m = m.group()
        if m in pattern:
            return True, m
        else:
            return False, ""


# 获取缺陷commit
def git_bug_commit():
    with open(os.path.join(result_root, "diff.txt"), "r", encoding="utf-8") as fr:
        lines = fr.readlines()
    tLine = list()
    data = list()
    cnt = 0
    isBug = False
    pattern = read_bugId()

    for line in lines:
        tmp = re.split(r"\s+", line.strip())
        if len(tmp) > 0:
            if is_num(tmp[0]):
                tLine[2].append(tmp[2])
                cnt = 1
            elif isSHA(tmp[0]):
                if len(tLine) > 0 and cnt > 0:
                    if isBug:
                        data.append(tLine)
                isBug, BugId = check_bug_exist(" ".join(tmp[1:]), pattern)
                cnt = 0
                tLine = list()
                tLine.append(tmp[0])
                tLine.append(" ".join(tmp[1:]))
                tLine.append(list())
                tLine.append(BugId)
            else:
                pass
    if len(tLine) > 0 and cnt > 0:
        if isBug:
            data.append(tLine)

    with open(os.path.join(result_root, "commit_bugId.csv"), "w", encoding="utf-8", errors="ignore") as fr:
        for d in data:
            fr.write(d[0] + "," + d[3] + "," + d[1] + "\n")
    return data


# 获取diff文件
def git_diff_file(data):
    if not os.path.exists(os.path.join(result_root, "diff/")):
        os.mkdir(os.path.join(result_root, "diff/"))
    for item in data:
        tmp = item[0] + ".txt"
        os.system("git log -p -n 1 --full-index {} > {}".format(item[0], os.path.join(result_root, "diff/" + tmp)))


# 仅分析.java文件的变更
def screen_changed_file(data):
    new_data = list()
    for item in data:
        new_item = list()
        new_item.append(item[0])
        new_item.append(list())
        for file in item[2]:
            if file[-5:] == ".java":
                new_item[1].append(file)
        if len(new_item[1]) != 0:
            new_data.append(new_item)
    return new_data


# 根据file lines 追溯引入缺陷的commit
def git_blame_file_with_commit(file, lines):
    os.system("git blame --abbrev=7 {} > {}".format(file, os.path.join(result_root, "temp.txt")))
    with open(os.path.join(result_root, "temp.txt"), encoding="utf-8", errors="ignore") as fr:
        res = fr.readlines()
    ans = list()
    for line in lines:
        if line > len(res):
            logging.warning("git blame line error! " + file + ":" + line)
            continue
        tmp = res[line - 1].strip()
        tmps = re.split("\s+", tmp)

        tmp2 = "".join(tmps)
        if tmp2.find(')') == len(tmp2) - 1:
            continue

        if len(tmps) > 0:
            ans.append([line, tmps[0]])
    os.remove(os.path.join(result_root, "temp.txt"))
    return ans


# 定位有缺陷的file lines, 追溯引入缺陷的commit
def resolve_diff_file(data):
    fw = open(os.path.join(result_root, "bug_commits_lines_info.csv"), 'w', encoding="utf-8")
    for item in data:
        commitId = item[0]

        ## 只筛选出 后于 max_commit 的commit
        if max_commit != "" and commitWithTime[commitId] > commitWithTime[max_commit]:
            continue

        os.chdir(code_repository)
        os.system("git reset --hard {}~1".format(commitId))
        time.sleep(0.01)
        diff = open(result_root + "diff/" + item[0] + ".txt", 'r', encoding='UTF-8')
        try:
            bugFiles = parse_diff(diff)
        except:
            logging.warning("Cannot analyze diff " + result_root + "diff/" + item[0] + ".txt")
            continue
        for bugInfo in bugFiles:
            bug_lines_delete = bugInfo.hunk_infos['d']
            if len(bug_lines_delete) == 0:
                continue
            src_file = bugInfo.src_file[2:]
            if src_file[-5:] != ".java":
                continue
            res = git_blame_file_with_commit(src_file, bug_lines_delete)
            for rp in res:
                fw.write(commitId + "," + src_file + "," + str(rp[0]) + "," + rp[1] + "\n")
    fw.close()
    os.system("git reset --hard {}".format(commitWithIndex[0]))


git_commit_info(project, branch_name)
git_file_change()
data = git_bug_commit()
git_diff_file(data)
data = screen_changed_file(data)
resolve_diff_file(data)