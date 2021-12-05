<script>
	import { onMount } from 'svelte';

	// import { Terminal } from 'xterm';
	// import { FitAddon } from 'xterm-addon-fit';

	let config = {
		pop: 30,
		gen: 20,
		k: 30,
		s: 20,
		operator_flip: 60,
		switch_branches: 30,
		switch_exp: 70,
		truncate_node: 25
	}

	let current_gen = [];
	let hallOfFame = []
	let generationNumber = null;
	let currentBest = null;

	let log = "";
	let fullScreenTerminal = false;

	let running = false;

	let individualsPoller;
	let logPoller;

	const labels = [];
	const data = {
		labels: labels,
		datasets: [{
			label: 'Fitness',
			data: [],
			borderColor: '#ccc',
			fill: false,
			cubicInterpolationMode: 'monotone',
			tension: 0.4,
		}]
	};

	const configChart = {
		type: 'line',
		data: data,
		options: {
			responsive: true
		}
	};

	let fitnessChart;

	// const term = new Terminal({convertEol: true});
	// const fitAddon = new FitAddon();
	// term.loadAddon(fitAddon);

	onMount(() => {
		// document.getElementById('terminal').innerHTML = "";

		
		// term.open(document.getElementById('terminal'));	
		// fitAddon.fit();
		bulmaToast.setDefaults({
			duration: 2000,
			position: 'bottom-right',
			closeOnClick: true,
			animate: { in: 'fadeIn', out: 'fadeOut' }
		})


		// chart

		fitnessChart = new Chart(
			document.getElementById('fitnessChart'),
			configChart
		);
	})

	async function saveConfig() {
		let file = new Blob([JSON.stringify(config)], {type: 'text/plain'});
		// window.open(URL.createObjectURL(file));
		let filename = 'params.pyGENP';
		if (window.navigator.msSaveOrOpenBlob) // IE10+
			window.navigator.msSaveOrOpenBlob(file, filename);
		else { // Others
			var a = document.createElement("a"),
					url = URL.createObjectURL(file);
			a.href = url;
			a.download = filename;
			document.body.appendChild(a);
			a.click();
			
			setTimeout(function() {
				document.body.removeChild(a);
				window.URL.revokeObjectURL(url);  
			}, 0); 
		}
	}

	function loadConfig(e) {
		var file = e.target.files[0];
		if (!file) {
			return;
		}
		var reader = new FileReader();
		reader.onload = function(e) {
			var contents = e.target.result;
			config = JSON.parse(contents);
		};
		reader.readAsText(file);
		bulmaToast.toast({ message: "Imported!", type: 'is-primary' });
	}

	async function cleanMemory() {
		clearInterval(individualsPoller);
		clearInterval(logPoller);
		current_gen = [];
		generationNumber = null;
		currentBest = null;
		const res = await fetch('/clean');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		// alert(result.msg);
		bulmaToast.toast({ message: result.msg, type: 'is-primary' });
	}

	async function cleanNS3() {
		const res = await fetch('/ns3reset');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		// alert(result.msg);
		bulmaToast.toast({ message: result.msg, type: 'is-primary' });
	}

	async function run() {
		const res = await fetch('/run', {
			method: 'POST',
			headers: {
				'Accept': 'application/json',
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(config)
		});
		if (res.status == 200)
			running = true;
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		// alert(result.msg);
		bulmaToast.toast({ message: result.msg, type: 'is-primary' });

		individualsPoller = setInterval(getCurrentGen, 3000);
		logPoller = setInterval(getLog, 2000);
	}

	async function getCurrentGen() {
		const res = await fetch('/gen/current');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		if (result.individuals) {
			result.individuals.sort((a, b) => a.id > b.id ? 1 : -1);
			current_gen = result.individuals;
			
			current_gen.forEach((item) => {
				let fit = parseFloat(item.fitness);
				if (fit > 0 && (currentBest == null || fit > currentBest)) {
					currentBest = fit;
				}
			})

			if (current_gen.length > 0 
				&& (generationNumber == null 
					|| parseInt(current_gen[0].gen) > generationNumber)) {
					generationNumber = parseInt(current_gen[0].gen);
					currentBest = null;
					getHallOfFame();
			}
		}
		// alert(result.msg);
		// bulmaToast.toast({ message: result.msg, type: 'is-primary' });
	}

	async function getHallOfFame() {
		const res = await fetch('/hall');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		if (result.individuals) {
			hallOfFame = result.individuals;

			let xDataLabels = Array.from({length: hallOfFame.length}, (_, i) => i + 1);
			let yData = [];
			for (let i of hallOfFame) {
				yData.push(i.fitness);
			}

			fitnessChart.data.datasets = [{
				label: 'Fitness',
				data: yData,
				borderColor: '#ccc',
				fill: false,
				cubicInterpolationMode: 'monotone',
				tension: 0.4,
			}];
			fitnessChart.data.labels = xDataLabels;
			fitnessChart.update();

		}


	}

	async function getLog() {
		const res = await fetch('/log');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		log = result.buffer;
		
		document.getElementById('terminal').innerHTML = "";

		const term = new Terminal({convertEol: true});
		term.setOption('fontSize', 15);
		term.reset();
		term.open(document.getElementById('terminal'));	
        term.write(log);
	}

	
	getLog()
</script>




<main>

	<div class="nav-bar">
		pyGENP
	</div>

	<!-- <p style="text-align: left;">
		Welcome to pyGENP TCP Congestion Control Tool!
	</p> -->

	<div style="display:flex;justify-content: left;padding: 1rem;">
		<button class="button" class:running={running} on:click={() => run()}>
			<span class="material-icons">
				{#if running}
					pause
				{:else}
					play_arrow
				{/if}
			</span>			
			Run
		</button>

		{#if running}
		<button class="button btn-stop" on:click={() => {running = false; cleanMemory()}}>
			<span class="material-icons">
				stop
			</span>			
			Stop Run
		</button>
		{/if}
		<!-- <button class="button" on:click={() => getCurrentGen()}>
			<span class="material-icons">
				play_arrow
			</span>			
			Current Gen
		</button> -->
		<button class="button" on:click={() => saveConfig()}>
			<span class="material-icons">
				save
			</span>			
			Save Params
		</button>
		<label class="button">
			<input type="file" accept=".pyGENP" style="display: none;" on:change={(e) => loadConfig(e)}>
			<span class="material-icons">
				cloud_upload
			</span>			
			Load Params
		</label>
		<button class="button" on:click={() => cleanMemory()}>
			<span class="material-icons">
				cleaning_services
			</span>			
			Clean Memory
		</button>
		<button class="button" on:click={() => cleanNS3()}>
			<span class="material-icons md-18">
				restart_alt
			</span>			
			NS3 Clean
		</button>
	</div>

	<div class="columns" style="text-align: left;">
		<div class="column" style="min-width: 250px !important;">
			<span style="padding: 1rem;">
				Parameters
			</span>
			<div style="padding: 1rem;padding-right: 0;font-size: .8rem">

				<div style="padding-bottom: .2rem; font-weight: 800">General</div>

				<div class="params">
					<div>Population Size</div>
					<input type="text" placeholder="eg. 30" bind:value={config.pop}>
				</div>

				<div class="params">
					<div>Generations</div>
					<input type="text" placeholder="eg. 15" bind:value={config.gen}>
				</div>

				<div style="padding-bottom: .2rem; font-weight: 800">Tournament Selection</div>

				<div class="params">
					<div class="dropdown is-hoverable">
						<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-ksample">
							K Individuals
						</div>
						<div class="dropdown-menu" id="dropdown-ksample" role="menu">							
							<div class="dropdown-content">
							  <div class="dropdown-item">
								how many individuals to randomly select from population.
							  </div>
							</div>
						</div>
					</div>
					<input type="text" placeholder="eg. 20" bind:value={config.k}>
				</div>

				<div class="params">
					<div class="dropdown is-hoverable">
						<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-ssample">
							S Individuals
						</div>
						<div class="dropdown-menu" id="dropdown-ssample" role="menu">							
							<div class="dropdown-content">
							  <div class="dropdown-item">
								how many individuals to select if minimum fitness requirement is met.
							  </div>
							</div>
						</div>
					</div>
					<input type="text" placeholder="eg. 15" bind:value={config.s}>
				</div>

				<div style="padding-bottom: .2rem; font-weight: 800">Mutation (in %)</div>

				<div class="params">
					<div class="dropdown is-hoverable">
						<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-box">
							Operator Flip
						</div>
						<div class="dropdown-menu" id="dropdown-box" role="menu">							
							<div class="dropdown-content">
							  <div class="dropdown-item">
								Probability to mutate an individual.
							  </div>
							</div>
						</div>
					</div>
					<input type="text" placeholder="eg. 20" bind:value={config.operator_flip}>
				</div>

				<div class="params">
					<div class="dropdown is-hoverable">
						<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-box">
							Switch Branches
						</div>
						<div class="dropdown-menu" id="dropdown-box" role="menu">							
							<div class="dropdown-content">
							  <div class="dropdown-item">
								Probability to switch branches if it is a IfThenElse operator.
							  </div>
							</div>
						</div>
					</div>
					<input type="text" placeholder="eg. 20" bind:value={config.switch_branches}>
				</div>

				<div class="params">
					<div class="dropdown is-hoverable">
						<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-box">
							Switch Exp
						</div>
						<div class="dropdown-menu" id="dropdown-box" role="menu">							
							<div class="dropdown-content">
							  <div class="dropdown-item">
								Probability to switch compatible expressions like sum and multiplication.
							  </div>
							</div>
						</div>
					</div>
					<input type="text" placeholder="eg. 20" bind:value={config.switch_exp}>
				</div>

				<div class="params">
					<div class="dropdown is-hoverable">
						<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-box">
							Truncate Node
						</div>
						<div class="dropdown-menu" id="dropdown-box" role="menu">							
							<div class="dropdown-content">
							  <div class="dropdown-item">
								Probability to mutate with truncation an individual.
							  </div>
							</div>
						</div>
					</div>
					<input type="text" placeholder="eg. 20" bind:value={config.truncate_node}>
				</div>


			</div>
		</div>
		<div class="column is-four-fifths">
			<span style="padding: 1rem;padding-left:0;">
				🧬 Current Generation Individuals 🧬
			</span>
			<div class="individual-container">
				{#each current_gen as ind}
					<div class="ind" style="text-align: left;">
						<div style="width: 20%">{ind.id}</div>
						<div style="width: 30%;text-align:center;">{ind.path}</div>
						<div style="width: 25%;text-align:right;">{ind.time.toFixed(2)} seconds</div>
						<div style="width: 25%;text-align:right;">{ind.fitness.toFixed(2)} Mbit/s</div>
					</div>
				{/each}
			</div>
		</div>
	</div>

	<div class="columns">
		<div class="column" style="text-align: left;padding-left: 1.8rem;">
			🧬 <b>Generation:</b> {generationNumber || 'n.a.'} / {config.gen} 
		</div>
		<div class="column">
			🥇 <b>Current Best:</b> {currentBest?.toFixed(2) || 0} Mbit/s
		</div>
		<div class="column is-half" style="margin: auto;">			
			<div style="display: flex; align-items: center; justify-content: space-between;">
				<div>{((current_gen.length/config.pop)*100).toFixed(0)}%</div>
				<div class="progress-bar" style="width: 88%;">
					<div class="progress-bar-thumb" style="width: {(current_gen.length/config.pop)*100}%;"></div>
				</div>
			</div>
		</div>
	</div>


	<div class="columns">
		<div class="column">
			<span style="padding: 1rem;padding-left:0;">
				📈 Chart Statistics
			</span>
			<div style="padding: 2rem;padding-top:0.5rem;">
				<canvas id="fitnessChart"></canvas>
			</div>
		</div>
		<div class="column is-one-fourth">
			<span style="padding: 1rem;padding-left:0;">
				🏆 Hall of Fame Individuals 🏆
			</span>
			<div class="individual-container">
				{#each hallOfFame as ind}
					<div class="ind" style="background:#f1eb2e!important;color:#424242!important;">
						<div style="width: 33.3%;text-align: left;">{ind.id}</div>
						<div style="width: 33.3%;text-align:center;">{ind.gen} Generation</div>
						<div style="width: 33.3%;text-align:right;">{ind.fitness.toFixed(2)} Mbit/s</div>
					</div>
				{/each}
			</div>
		</div>
	</div>

	

	<div style="height:6rem;padding:2rem;">

	</div>
	

	<div class="console-container">
		<div style="margin: 0 0 0 1rem;display:flex; justify-content: space-between;align-items: center;">
			Console log
			<button class="button" on:click={() => {
				if (fullScreenTerminal) {
					document.getElementById('cons-container').style.height = "3rem";
					fullScreenTerminal = false;
				} else {
					document.getElementById('cons-container').style.height = "25rem";
					fullScreenTerminal = true;
				}
			}}>
				<span class="material-icons">
					aspect_ratio
				</span>	
				{#if fullScreenTerminal}
					Collapse
				{:else}		
					Expand
				{/if}
			</button>
		</div>
		<!-- <div id="dragbar" style="cursor: n-resize; height: 0.25rem; background-color: #3c3c3c;">

		</div> -->
		<div id="cons-container" class="console">
			<!-- <pre>
				{log}
			</pre> -->
			<div id="terminal"></div>
		</div>
	</div>
	

	
</main>

<style>
	.progress-bar {
		background-color: #3c3c3c;
		border-radius: 1rem;
		height: .4rem;
		margin-right: 2.5rem;
		overflow: hidden;
	}
	.progress-bar-thumb {
		background-color: #ccc;
		width: 0%;
		height: .4rem;
		border-radius: 1rem;
	}

	.running {
		background: #259743 !important;
		color: #ffffff !important;
		pointer-events: none;
	}
	.ind {
		display: flex;
		justify-content: space-between;
		font-size: 0.8rem;
		padding: 0rem 0.5rem;
		border-radius: 0.2rem;
		width: 100%;
		background: #2f6e60;
		margin-bottom: 0.4rem;
		color: #c7c7c7;
		font-weight: 800;
		box-shadow: 0 0.1rem 0.5rem #343434;
	}
	.dropdown-content {
		background: #242424;
		padding: 0;
		width: 20rem;
	}
	.dropdown-item {
		padding: 0.5rem;
		color: #838383;
		text-align: left;
	}
	.params {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
	}
	.params input {
		width: 6rem;
		text-align: right;
	}
	.console-container {		
		position: fixed;
		/* width: 48rem; */
		width: 100%;
		bottom: 0rem;
		right: 0;
		border-radius: .35rem .35rem 0 0;
		text-align: left;
		background: #000;
		padding: 0.5rem;
		padding-top: 1rem;
	}
	.console {
		/* padding: 1rem; */
		padding: 0 1rem;
		padding-right: 0;
		font-size: .8rem;
		line-height: 1rem; 
		height: 3rem; 
		width: 100%; 
		/* overflow-y: auto; */
		overflow: hidden;
		background: #000;
		/* resize: vertical; */
	}
	.individual-container {
		border-radius: 0.3rem;
		background-color: #3c3c3c;
		padding: 1rem;
		margin: 1rem;
		margin-left: 0rem;
		margin-right: 2.5rem;
		height: 20rem;
		overflow-y: auto;
	}
	p {
		padding: 1rem;
	}
	.nav-bar {
		display: flex;
		justify-content: center;
		background: #262626;
    	color: #e9e9e9;
		font-size: 1.2rem;
		padding: 1rem;
		font-weight: 800;
	}
	main {
		text-align: center;
		padding: 0;
		margin: 0;
		margin: 0 auto;
		height: 100%;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>