import os
import re
import logging
from diff_parser import parse_diff


project = "accumulo"
branch_name = "master"


code_repository = "E:/Bug_Collection/Code_Repository/"
code_repository = os.path.join(code_repository, project + "/")
result_root = "E:/Bug_Collection/Bug_Collection_Results/"
result_root = os.path.join(result_root, project + "/" + branch_name + "/")
version_root = "E:/Bug_Collection/Version_Info/"
version_root = os.path.join(version_root, project + ".csv")

commit_version = dict()
commitWithTime = {}
commitAll = []


def read_version():
    with open(version_root, 'r', encoding='utf-8') as fr:
        lines = fr.readlines()
    for line in lines:
        if line.strip():
            line = line.strip()
            spices = line.split(",")
            if spices[0] == branch_name:
                v_c = spices[2][:8]
                v_n = spices[1]
                commit_version[v_c] = v_n


def get_commit_info():
    with open(os.path.join(result_root, "commit_ref.txt"), "r", encoding="utf-8") as fr:
        lines = fr.readlines()
    cnt = 0
    for line in lines:
        line = re.split("\s+", line.strip())
        commitWithTime[line[0][:8]] = cnt
        commitAll.append(line[0][:8])
        cnt += 1


def get_version_line(delete_lines, add_lines, line):
    if line in delete_lines:
        return -1
    t = line - len([x for x in delete_lines if x<line])
    for x in add_lines:
        if x <= t:
            t += 1
    return t


def get_commit_version():
    with open(os.path.join(result_root, "bug_commits_lines_info.csv"), "r", encoding="utf-8") as fr:
        lines = fr.readlines()
    os.chdir(code_repository)
    bug_commit_version = list()
    bug_commit_version_line_info = list()
    cmd_temp = ""

    for k, v in commit_version.items():

        for strline in lines:
            strline = strline.strip()
            temp = strline.split(",")
            commitId = temp[0][:8]
            commitStart = temp[3]
            file_path = temp[1]
            target_line = temp[2]

            if commitStart[0:1] == "^":
                for c in commitAll:
                    if commitStart == ("^" + c[0:7]):
                        commitStart = c
                        break
            
            if commitStart not in commitWithTime.keys():
                logging.warning("Can not find the commitId: " + commitStart)
                continue

            # after commitStart and before commitId
            if commitWithTime[k] <= commitWithTime[commitStart] and commitWithTime[k] > commitWithTime[commitId]:
                if cmd_temp != "git diff {}~1 {} -- {} > {}".format(commitId, k, file_path, os.path.join(result_root, "version_diff_temp.txt")):
                    cmd_temp = "git diff {}~1 {} -- {} > {}".format(commitId, k, file_path, os.path.join(result_root, "version_diff_temp.txt"))
                    print(cmd_temp)
                    os.system(cmd_temp)

                diff = open(os.path.join(result_root, "version_diff_temp.txt"), 'r', encoding="utf-8")

                # 当产生的diff文件不为空时, 需要对目标行进行重定位
                if os.path.getsize(os.path.join(result_root, "version_diff_temp.txt")):
                    try:
                        version_diff = parse_diff(diff)

                        # 当解析前后的版本中文件路径发生变更时，暂不考虑
                        if version_diff[0].tar_file == "/dev/null":
                            continue
                        delete_lines = version_diff[0].hunk_infos['d']
                        add_lines = version_diff[0].hunk_infos['a']
                        version_line = get_version_line(delete_lines, add_lines, int(target_line))
                    except:
                        logging.warning("Cannot analyze diff")
                        continue
                else:
                    version_line = target_line

                bug_commit_version_line_info.append("" + commitId + "," + file_path + "," + target_line + "," + v + "," + str(version_line))
                bug_commit_version.append(strline + "," + v)

    with open(os.path.join(result_root, "bug_commits_lines_versions_info.csv"), "w", encoding="utf-8") as fr:
        for line in bug_commit_version:
            fr.write(line + "\n")
    with open(os.path.join(result_root, "bug_commits_lines_versions_lines_info.csv"), "w", encoding="utf-8") as fr:
        for line in bug_commit_version_line_info:
            fr.write(line + "\n")


read_version()
get_commit_info()
get_commit_version()
