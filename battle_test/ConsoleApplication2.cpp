
#include <string.h>
#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <sstream>
#include <fstream>
#include <string>
using namespace std;


ofstream outfile;

int execmd(char* cmd, char* result) {
	char buffer[128];
	FILE* pipe = _popen(cmd, "r");
	if (!pipe)
		return 0;
	while (!feof(pipe)) {
		if (fgets(buffer, 128, pipe)) {
			strcat(result, buffer);
		}
	}
	_pclose(pipe);
	return 1;
}
int main() {
	ofstream out("../log/result_many.txt");
	out << endl;
	out.close();

	int k;
	cout << "loop count: ";
	cin >> k;
	for (int i = 0; i < k; i++) {
		ofstream o("../log/result_many.txt", ios::app);
		o << "-------------- Battle: " << i + 1 << " ----------------\n";
		system("cd /d C:/Users/chier/Desktop/huawei_ai/client & python -m ballclient.main 1001 127.0.0.1 6001 > ../log/tmp_score.txt");

		char result[1024 * 4] = "";
		if (1 == execmd("cd /d C:/Users/chier/Desktop/huawei_ai/server & BattleServer.exe map_r2m1.txt 127.0.0.1 6001", result)) {
			o << result << endl;
		}
		o.close();
		Sleep(2000);
	}

	return 0;
}
