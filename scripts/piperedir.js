/*
 * The script creates Windows named pipe server "\\.\pipe\log" and redirects all
 * incoming data to stdout.
 */

const net = require('net');

const connection_path = process.argv[2] || '\\\\.\\pipe\\log';

let server = net.createServer()
	.on('error', error => {
		console.error('Server error: ', error);
		process.exit(99);
	})
	.on('listening', () => {
		//console.log('Server listening');
	})
	.on('connection', socket => {
		//console.log('Server connected');
		socket
			.on('close', hadError => {
				if (hadError) {
					console.error('Server closed with error.');
				}
			})
			.on('data', data => {
				process.stdout.write(data);
			})
			.on('error', error => {
				console.error('Server error: ', error);
				process.exit(99);
			})
			.resume();
	})
	.on('close', () => {
		console.log('Server closed');
	});

server.listen(connection_path);
