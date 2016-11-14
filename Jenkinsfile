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
  			sh 'sudo pip install virtualenv'
  		}
  
  		stage ('Create Test Results Folder') {
  			sh 'mkdir -p test_results'
  		}
  
  		stage ('Setup virtualenv') {
  			sh 'virtualenv -p python3 venv'
  			source venv/bin/activate
  		}
  
  		stage ('Install pip dependencies') {
  			sh 'pip3 install -r --upgrade requirements.txt'
  		}
  
  		stage ('Build Applications') {
  			sh 'scripts/build.sh > test_results/build_app.txt'
  		}
  
  		stage ('Run python linter') {
  			sh 'pep8 dipla'
  			sh 'pep8 tests'
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
