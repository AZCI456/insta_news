#include <filesystem>

#ifdef _WIN32
    #define CONFIG_PATH "%APPDATA%\\app_name\\"
#else // __APPLE__, Linux
    #define CONFIG_PATH "~/.config/insta_news"
#endif

using namespace fs = std::filesystem;

int main(){

	fs::path config_folder(CONFIG_PATH);

	std::string USERNAME;
	while (true){
		std::cin 
	} 
}