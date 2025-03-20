import os

assert os.path.exists("./bin/generation/student/")
assert os.path.exists("./bin/generation/docker/gradescope/")
assert os.path.exists("./bin/generation/prairielearn/")

assert os.path.exists("./bin/generation/docker/gradescope/run_autograder")
assert os.path.exists("./bin/generation/docker/gradescope/setup.sh")
assert os.path.exists("./bin/generation/docker/gradescope/config.toml")
assert os.path.exists("./bin/generation/prairielearn/tests/run_autograder")
assert os.path.exists("./bin/generation/prairielearn/tests/config.toml")

actual_gs_dirs = os.listdir("./bin/generation/docker/gradescope/")
actual_student_dirs = os.listdir("./bin/generation/student/")

docker_expected_test_files = [file for file in os.listdir("./student_tests/") if os.path.isfile(os.path.join("student_tests", file))]
docker_expected_test_files.sort()

student_expected_files = [file for file in docker_expected_test_files if "test_public" in file]
student_expected_files.sort()

gs_actual_test_files = [file for file in os.listdir("./bin/generation/docker/gradescope/student_tests/") if os.path.isfile(os.path.join("./bin/generation/docker/gradescope/student_tests/", file))]
gs_actual_test_files.sort()
pl_actual_test_files = [file for file in os.listdir("./bin/generation/prairielearn/tests/student_tests/") if os.path.isfile(os.path.join("./bin/generation/prairielearn/tests/student_tests/", file))]
pl_actual_test_files.sort()

student_actual_files = [file for file in os.listdir("./bin/generation/student/student_tests/") if os.path.isfile(os.path.join("./bin/generation/student/student_tests/", file))]
student_actual_files.sort()


assert docker_expected_test_files == gs_actual_test_files
assert docker_expected_test_files == pl_actual_test_files
assert student_expected_files == student_actual_files

expected_starter_code = os.listdir("./starter_code/")

actual_starter_code = os.listdir("./bin/generation/student/student_work/")
actual_starter_code = [file for file in actual_starter_code if file[-3:] == ".py"]

assert len(actual_starter_code) == 1
assert expected_starter_code == actual_starter_code

actual_starter_code = os.listdir("./bin/generation/prairielearn/")
actual_starter_code = [file for file in actual_starter_code if file[-3:] == ".py"]

assert len(actual_starter_code) == 1
assert expected_starter_code == actual_starter_code

# assert that it did not get pulled in to docker
assert not os.path.exists("./bin/generation/docker/gradescope/starter_code/")


expected_public = os.listdir("./student_tests/data/files/test_public/")
expected_public.sort()

expected_private = os.listdir("./student_tests/data/files/test_private/")
expected_private.sort()

docker_expected_directories = ["test_public", "test_private"]
docker_expected_directories.sort()

student_expected_directories = ["test_public"]

gs_actual_directories = os.listdir("./bin/generation/docker/gradescope/student_tests/data/files/")
gs_actual_directories.sort()

pl_actual_directories = os.listdir("./bin/generation/prairielearn/tests/student_tests/data/files/")
pl_actual_directories.sort()

student_actual_directories = os.listdir("./bin/generation/student/student_tests/data/files/")

assert docker_expected_directories == gs_actual_directories
assert docker_expected_directories == pl_actual_directories
assert student_expected_directories == student_actual_directories

student_actual_files_data_folder = os.listdir("./bin/generation/student/student_tests/data/files/test_public/")
student_actual_files_data_folder.sort()

assert expected_public == student_actual_files_data_folder

student_student_work_folder = os.listdir("./bin/generation/student/student_work/")

for file in expected_public:
    assert file in student_student_work_folder

for file in expected_private:
    assert file not in student_student_work_folder


gs_actual_public_files = os.listdir("./bin/generation/docker/gradescope/student_tests/data/files/test_public")
gs_actual_public_files.sort()

gs_actual_private_files = os.listdir("./bin/generation/docker/gradescope/student_tests/data/files/test_private")
gs_actual_private_files.sort()

pl_actual_public_files = os.listdir("./bin/generation/prairielearn/tests/student_tests/data/files/test_public")
pl_actual_public_files.sort()

pl_actual_private_files = os.listdir("./bin/generation/prairielearn/tests/student_tests/data/files/test_private")
pl_actual_private_files.sort()

assert gs_actual_private_files == expected_private
assert gs_actual_public_files == expected_public
assert pl_actual_private_files == expected_private
assert pl_actual_public_files == expected_public

