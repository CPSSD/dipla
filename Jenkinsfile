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
        sh 'sudo apt-get install --upgrade -y python3'
        sh 'sudo apt-get install --upgrade -y python3-pip'
        //sh 'sudo pip3 install virtualenv'
      }
  
      stage ('Create Test Results Folder') {
        sh 'mkdir -p test_results'
      }
  
      stage ('Setup virtualenv') {
        //sh 'virtualenv -p python3 venv'
        //sh 'source venv/bin/activate'
      }
  
      stage ('Install pip dependencies') {
        sh 'pip3 install --upgrade -r requirements.txt'
      }
  
      stage ('Run python linter') {
        sh 'pep8 dipla'
        sh 'pep8 tests'
      }
 
      stage ('Build example binaries') {
        sh 'tests/example_binaries/build_binaries.sh'
      }
 
      stage ('Run Tests') {
        sh 'nosetests -v'
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
