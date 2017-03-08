import org.gradle.api.Plugin
import org.gradle.api.Project


class VocPlugin implements Plugin<Project> {
    void apply(Project project) {
        project.extensions.create("voc", VocPluginExtension)

        project.task('vocBuild') {
            doLast {
                 if (project.voc.buildFromSourceDir) {
                    def jarPath = "./dist/android/libs/python-android-support.jar"
                     project.exec {
                         workingDir "${project.voc.buildFromSourceDir}"
                         commandLine 'ant android'.split()
                     }
                     project.exec {
                         commandLine "cp ${jarPath} libs/".split()
                     }
                 }
                project.exec {
                    println "_________________________________________"
                    println "voc.sourcesDir: ${project.voc.sourcesDir}"
                    println "voc.namespace: ${project.voc.namespace}"
                    println "_________________________________________"
                    // TODO: compile a directory instead of a hardcoded module
                    commandLine "voc -v ${project.voc.sourcesDir} -o libs -n ${project.voc.namespace}".split()
                }
                project.exec {
                    workingDir 'libs'
                    commandLine "jar cvf python-app.jar ${project.voc.namespace.replace('.', '/')}".split()
                }
            }
        }

        project.task('runAndroidVocApp') {
            doLast {
                project.exec {
                    commandLine "adb shell am start -n ${project.voc.namespace}/android.PythonActivity".split()
                }
            }
        }
    }
}


class VocPluginExtension {
    String namespace = "com.example"
    def sourcesDir
    def buildFromSourceDir
}
