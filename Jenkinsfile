#!groovy

node {

  timeout(30) {
  
    currentBuild.result = 'SUCCESS'
  
    stage ('Alert Github and Slack') {
      step([$class: 'GitHubSetCommitStatusBuilder'])
    }
  
    stage('Clean Last Build') {
      sh('rm -rf *')
    }
  
    stage ('Clone Repository') {
      checkout scm
    }
  
    try {
      stage ('Install Dependencies') {
        // Dependenceies already present on CI server and deadsnakes repo dead
        //sh 'sudo add-apt-repository ppa:fkrull/deadsnakes'
        //sh 'sudo apt-get update'
        //sh 'sudo apt-get install -y python3.5'
        //sh 'sudo python3.5 -m "pip" install virtualenv'
      }
  
      stage ('Create Test Results Folder') {
        sh 'mkdir -p test_results'
      }
  
      stage ('Setup virtualenv') {
        //sh 'virtualenv -p python3.5 venv'
        //sh 'source venv/bin/activate'
      }
  
      stage ('Install pip dependencies') {
        sh 'python3.5 -m easy_install pip'
        sh 'python3.5 -m pip install --upgrade -r requirements.txt'
      }
  
      stage ('Run python linter') {
        sh 'pep8 dipla'
        sh 'pep8 tests'
      }
 
      stage ('Build example binaries') {
        sh 'tests/example_binaries/build_binaries.sh'
      }
 
      stage ('Run Tests') {
        sh 'python3.5 -m "nose" -v'
      }
  
      stage ('Generate Reports') {
        step([$class: 'GitHubCommitStatusSetter'])
      }
  
    } catch (err) {
      currentBuild.result = 'FAILURE'
      throw err
    }
  }
}
