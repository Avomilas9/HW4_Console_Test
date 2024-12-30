from checkers import checkout, getout
import yaml
from sshcheckers import ssh_checkout, upload_files, ssh_getout

with open('config.yaml') as f:
    data = yaml.safe_load(f)

class TestPositive:

    def save_log(self, starttime, name):
        with open(name, 'w') as f:
            f.write(getout("journalctl --since '{}'".format(starttime)))

    def test_step1(self, create_folders, clear_folders, create_files, start_time):
        # Проверка добавления файлов в архив и наличия файла с архивом в папке
        res1 = ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z a {}/arx4 -t{}".format(data["folder_in"], data["folder_out"], data["type"]), "Everything is Ok")
        res2 = ssh_checkout(data["ip"], data["user"], data["passwd"], "ls {}".format(data["folder_out"]), "arx4.{}".format(data["type"]))
        self.save_log(start_time, "log1.txt")
        assert res1 and res2, "test1 - файлы не добавлены в архив или файл с архивом отсутствует в указанной папке"

    def test_step2(self, clear_folders, create_files, start_time):
        # Проверка распаковки архива и наличие распакованных файлов в папке
        res = []
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z a {}/arx -t{}".format(data["folder_in"], data["folder_out"], data["type"]), "Everything is Ok"))
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z e arx.{} -o{} -y".format(data["folder_out"], data["type"], data["folder_ext"]), "Everything is Ok"))
        for item in create_files:
            res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "ls {}".format(data["folder_ext"]), item))
        self.save_log(start_time, "log2.txt")
        assert all(res), "test2 -  архив не распакован, или распакованных файлов нет в указанной папке"

    def test_step3(self, clear_folders, create_files, start_time):
        # Проверка вывода списка файлов (l)
        res = []
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z a {}/arx -t{}".format(data["folder_in"], data["folder_out"], data["type"]), "Everything is Ok"))
        for item in create_files:
            res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z l arx.{}".format(data["folder_out"], data["type"]), item))
        self.save_log(start_time, "log4.txt")
        assert all(res), "test3 - не удалось найти файлы в архиве"

    def test_step4(self, clear_folders, create_files, create_subfolder, start_time):
        # Проверка разархивирования с путями (x)
        res = []
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z a {}/arx -t{}".format(data["folder_in"], data["folder_out"], data["type"]), "Everything is Ok"))
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z x arx.{} -o{} -y".format(data["folder_out"], data["type"], data["folder_ext2"]), "Everything is Ok"))
        for item in create_files:
            res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "ls {}".format(data["folder_ext2"]), item))
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "ls {}".format(data["folder_ext2"]), create_subfolder[0]))
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "ls {}/{}".format(data["folder_ext2"], create_subfolder[0]), create_subfolder[1]))
        self.save_log(start_time, "log5.txt")
        assert all(res), "test4 - не удалось разархивировать с сохранением путей"

    def test_step5(self, clear_folders, create_files, start_time):
        # Проверка расчета хеша (h)
        res = []
        self.save_log(start_time, "log6.txt")
        for item in create_files:
            res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z h {}".format(data["folder_in"], item), "Everything is Ok"))
            com_7z = "{} {} {} cd {}; 7z h -{} {} | grep CRC32 | awk '{{print $4}}'".format(data["ip"], data["user"], data["passwd"], data["folder_in"], data["alg_hash"], item)
            res_hash = ssh_getout(data["ip"], data["user"], data["passwd"], "cd {}; crc32 {}".format(data["folder_in"], item)).upper()
            res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], com_7z, res_hash))
        assert all(res), "test5 - хеш файла не совпадает с ожидаемым значением"

    def test_step6(self, start_time):
        # Проверка удаления
        res = []
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z a {}/arx -t{}".format(data["folder_in"], data["folder_out"], data["type"]),"Everything is Ok"))
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "cd {}; 7z d arx.{}".format(data["folder_out"], data["type"]), "Everything is Ok"))
        self.save_log(start_time, "log7.txt")
        assert all(res), "test6 - не удалось удалить архив"

    def test_step7(self, start_time):
        res = []
        upload_files(data["ip"], data["user"], data["passwd"], data["pkgname"] + ".deb", "/home/{}/{}.deb".format(data["user"], data["pkgname"]))
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "echo '{}' | sudo -S dpkg -i /home/{}/{}.deb".format(data["passwd"], data["user"], data["pkgname"]),"Настраивается пакет"))
        res.append(ssh_checkout(data["ip"], data["user"], data["passwd"], "echo '{}' | sudo -S dpkg -s {}".format(data["passwd"], data["pkgname"]),"Status: install ok installed"))
        self.save_log(start_time, "log8.txt")
        assert all(res), "test7 - ошибка уставновки"