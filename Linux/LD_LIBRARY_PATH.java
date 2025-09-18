import java.io.File;

public class LD_LIBRARY_PATH {
	public static void main(String[] args) {
		for (String path : System.getProperty("java.library.path").split(File.pathSeparator)) {
			File file = new File(path);
			if (file.exists() && file.canWrite()) {
				System.out.println(path);
				break;
			}
			try {
				if (file.mkdirs()) {
					System.out.println(path);
					break;
				}
			} catch (Exception e) {
			}
		}
	}
}
