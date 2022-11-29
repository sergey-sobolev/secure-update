DISPLAY=

sys-packages:
	# sudo apt install -y docker-compose
	# sudo usermod -aG docker ${USER}
	sudo apt install python3-pip -y
	# WSL2 specific trick to prevent pip from hanging
	sudo pip -v install pipenv

broker:
	docker-compose -f kafka/docker-compose.yaml up -d

permissions:
	chmod u+x ./app/app.py
	chmod u+x ./downloader/downloader.py
	chmod u+x ./file_server/server.py
	chmod u+x ./manager/manager.py
	# chmod u+x ./manager-hacked/manager.py
	chmod u+x ./monitor/monitor.py
	chmod u+x ./storage/storage.py
	chmod u+x ./updater/updater.py
	chmod u+x ./verifier/verifier.py

pipenv:
	pipenv install -r requirements.txt

prepare: sys-packages permissions pipenv build run-broker

prepare-screen:
	# WSL specific preparation
	sudo /etc/init.d/screen-cleanup start


run-screen: run-app-screen run-monitor-screen run-manager-screen run-file-server-screen run-downloader-screen run-storage-screen run-verifier-screen run-updater-screen

build:
	docker-compose build

run-broker:
	docker-compose up -d su-zookeeper su-broker

run:
	docker-compose up -d

restart:
	docker-compose restart

stop:
	docker-compose stop

down:
	docker-compose down

logs:
	docker-compose logs -f --tail 100

stop-app:
	pkill flask

restart-app: stop-app run


run-monitor-screen:
	screen -dmS monitor bash -c "pipenv run python ./monitor/monitor.py config.ini"

run-monitor:
	pipenv run ./monitor/monitor.py config.ini


run-manager-screen:
	screen -dmS manager bash -c "pipenv run python ./manager/manager.py config.ini"

run-manager:
	pipenv run python ./manager/manager.py config.ini


run-hacked-manager:
	pipenv run python ./manager-hacked/manager.py config.ini

run-app:
	export FLASK_DEBUG=1; pipenv run ./app.py

run-app-screen:
	screen -dmS app bash -c "echo $(PWD); export FLASK_DEBUG=1; pipenv run python ./app/app.py"

run-file-server:
	export FLASK_DEBUG=1; pipenv run python ./file_server/server.py

run-file-server-screen:
	screen -dmS file-server bash -c "export FLASK_DEBUG=1; pipenv run python ./server.py"

run-downloader:
	pipenv run python downloader/downloader.py config.ini

run-downloader-screen:
	screen -dmS downloader bash -c "pipenv run python downloader/downloader.py config.ini"

run-verifier:
	pipenv run python verifier/verifier.py config.ini

run-verifier-screen:
	screen -dmS verifier bash -c "pipenv run python verifier/verifier.py config.ini"

run-storage:
	pipenv run python storage/storage.py config.ini

run-storage-screen:
	screen -dmS storage bash -c "pipenv run python storage/storage.py config.ini"

run-updater:
	pipenv run python updater/updater.py config.ini

run-updater-screen:
	screen -dmS updater bash -c "pipenv run python updater/updater.py config.ini"

clean:
	docker-compose down
	pipenv --rm
	rm -f Pipfile*	

test:
	pipenv run pytest -sv --reruns 5

delay: run
	# required for starting up all the containers
	sleep 20

delayed-test: delay test


complete-check: clean prepare build delayed-test