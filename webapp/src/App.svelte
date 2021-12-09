<script>
	import { onMount } from 'svelte';
	import { Rainbow, Moon, Diamonds } from 'svelte-loading-spinners';

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
		truncate_node: 25,
		max_mutations: 10,
		value_bottom_limit: -100,
		value_top_limit: 100,
		max_code_lines: 100,
		max_depth: 10,
		max_width: 10,
		alpha_vars: 15,
		max_branch_depth: 3,
		payload_size: 1500,
		simulation_time: 7,
		multi_mtu: false,
		mtu_bottom_limit: 100,
		mtu_upper_limit: 1600,
		mtu_step: 200,
		wildcards: [
			"ReduceCwnd (tcb);",
            "segmentsAcked = SlowStart (tcb, segmentsAcked);",
            "CongestionAvoidance (tcb, segmentsAcked);",
            "TcpLinuxCongestionAvoidance (tcb, segmentsAcked);"
		],
		variables: [
			"tcb->m_segmentSize",
			"tcb->m_cWnd",
			"segmentsAcked"
		]
	}

	let current_gen = [];
	let hallOfFame = [];
	let generationNumber = null;
	let baseline = null;
	let currentBest = null;
	let calculatingBaseline = false;
	let autofixing = false;
	let wildcardModalIsOpen = false;
	let variableModalIsOpen = false;

	let log = "";
	let fullScreenTerminal = false;

	let running = false;

	let settingsDisplay = "default"; // default, advanced, sim

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
			responsive: true,
			maintainAspectRatio: true,
			scales: {
				y: {
					display: true,
					text: 'Mbit/s'
				}
			}
		}
	};

	let fitnessChart;

	window.addEventListener("resize", () => {fitnessChart.resize()});

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

		// call on start
		getLog();
	})

	function resetDefaultParam() {
		config = {
			pop: 30,
			gen: 20,
			k: 30,
			s: 20,
			operator_flip: 60,
			switch_branches: 30,
			switch_exp: 70,
			truncate_node: 25,
			max_mutations: 10,
			value_bottom_limit: -100,
			value_top_limit: 100,
			max_code_lines: 100,
			max_depth: 10,
			max_width: 10,
			alpha_vars: 15,
			max_branch_depth: 3,
			payload_size: 1500,
			simulation_time: 7,
			multi_mtu: false,
			mtu_bottom_limit: 100,
			mtu_upper_limit: 1600,
			mtu_step: 200,
			wildcards: [
				"ReduceCwnd (tcb);",
				"segmentsAcked = SlowStart (tcb, segmentsAcked);",
				"CongestionAvoidance (tcb, segmentsAcked);",
				"TcpLinuxCongestionAvoidance (tcb, segmentsAcked);"
			],
			variables: [
				"tcb->m_segmentSize",
				"tcb->m_cWnd",
				"segmentsAcked"
			]
		}
	}

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
		bulmaToast.toast({ message: "Imported!", type: 'is-success' });
	}

	async function cleanMemory() {
		clearInterval(individualsPoller);
		clearInterval(logPoller);
		current_gen = [];
		generationNumber = null;
		currentBest = null;
		hallOfFame = [];
		fitnessChart.data.datasets = [{
			label: 'Fitness',
			data: [],
			borderColor: '#ccc',
			fill: false,
			cubicInterpolationMode: 'monotone',
			tension: 0.4,
		}];
		fitnessChart.data.labels = [];
		fitnessChart.update();
		const res = await fetch('/clean');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		// alert(result.msg);
		bulmaToast.toast({ message: result.msg, type: 'is-success' });
	}

	async function cleanNS3() {
		const res = await fetch('/ns3reset');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		// alert(result.msg);
		bulmaToast.toast({ message: result.msg, type: 'is-success' });
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
		bulmaToast.toast({ message: result.msg, type: 'is-success' });

		individualsPoller = setInterval(getCurrentGen, 15000);
		logPoller = setInterval(getLog, 5000);
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
		// bulmaToast.toast({ message: result.msg, type: 'is-success' });
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

	async function restoreSnaphot(e) {
		var file = e.target.files[0];
		if (!file) return;

		let formData = new FormData();     
		formData.append("snapshot", file);

		const res = await fetch('/snapshot/restore', {
			method: 'POST',
			body: formData
		});
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		if (result.config != null)
			config = result.config
		// alert(result.msg);
		bulmaToast.toast({ message: result.msg, type: 'is-success' });		
	}

	async function snapshot() {
		const res = await fetch(`/snapshot?config=${JSON.stringify(config)}`);
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		download(result?.filename, result?.zip);
		// alert(result.msg);
		bulmaToast.toast({ message: result.msg, type: 'is-success' });
	}

	async function baselineNS3() {
		calculatingBaseline = true;
		const res = await fetch('/ns3baseline');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		baseline = result.baseline;
		// alert(result.msg);
		bulmaToast.toast({ message: result.msg, type: 'is-success' });
		calculatingBaseline = false;
	}

	async function autofix() {
		autofixing = true;
		const res = await fetch('/autofix');
		const json = await res.json();
		let result = JSON.parse(JSON.stringify(json))
		bulmaToast.toast({ message: result.msg, type: 'is-success' });
		autofixing = false;
	}







	// utils
	function download(filename, data) {
		var element = document.createElement('a');
		element.setAttribute('href', 'data:text/plain;base64,' + data);
		element.setAttribute('download', filename);

		element.style.display = 'none';
		document.body.appendChild(element);

		element.click();

		document.body.removeChild(element);
	}

	
	
</script>




<main>

	<div class="nav-bar" style="align-items: flex-start;">
		<img src="pyGENP.svg" alt="logo" style="height: 2.2rem; padding-right: .5rem;">
		pyGENP
	</div>

	<!-- <p style="text-align: left;">
		Welcome to pyGENP TCP Congestion Control Tool!
	</p> -->

	<div style="display:flex;justify-content: left;padding: 1rem;">
		<button class="button" class:running={running} on:click={() => run()}>
			<span class="material-icons">
				{#if running}
					<Diamonds size="20" color="#FEFEFE" unit="px" duration="2s"></Diamonds>
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
		<label class="button">
			<input type="file" accept=".zip" style="display: none;" on:change={(e) => restoreSnaphot(e)}>
			<span class="material-icons">
				alt_route
			</span>			
			From Snapshot
		</label>
		<button class="button" on:click={() => snapshot()} disabled={!running}>
			<span class="material-icons">
				history
			</span>			
			Take Snapshot
		</button>
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
		<button class="button" on:click={() => baselineNS3()}>
			{#if !calculatingBaseline}
			<span class="material-icons md-18">
				flag
			</span>
			NS3 Baseline
			{:else}
			<Rainbow size="30" color="#FEFEFE" unit="px" duration="2s"></Rainbow>
			{/if}
		</button>
		<button class="button" on:click={() => autofix()}>
			{#if !autofixing}
			<span class="material-icons md-18">
				auto_fix_high
			</span>
			Autofix
			{:else}
			<Moon size="20" color="#FEFEFE" unit="px" duration="1s"></Moon>
			<span style="padding-left:.5rem">Fixing</span>
			{/if}
		</button>
	</div>

	<div class="columns" style="text-align: left;">
		<div class="column" style="min-width: 250px !important;">
			<div style="display: flex;justify-content:space-between;align-items: end;">
				<span style="padding: 0 1rem;">
					Parameters
				</span>
				<span style="padding: 0;font-size:1.2rem;cursor:pointer" class="material-icons md-24" on:click={() => resetDefaultParam()}>
					restart_alt
				</span>
			</div>
			<div style="padding: 1rem;padding-right: 0;padding-bottom: 0;font-size: .8rem;">

				<div style="height:23rem;background:#222222;border-radius: .35rem .35rem .35rem 0;padding:1rem;padding-bottom:.5rem">
					{#if settingsDisplay == 'default'}
					
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

					<div class="params">
						<div class="dropdown is-hoverable">
							<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-box">
								Max Mutations
							</div>
							<div class="dropdown-menu" id="dropdown-box" role="menu">							
								<div class="dropdown-content">
								<div class="dropdown-item">
									Max number of mutations.
								</div>
								</div>
							</div>
						</div>
						<input type="text" placeholder="eg. 20" bind:value={config.max_mutations}>
					</div>
					{:else if settingsDisplay == 'advanced'}
					
					<div style="padding-bottom: .2rem; font-weight: 800">Advanced</div>					
					
					<div class="params">
						<div>Values Range</div>
						<div>[</div>
						<input style="width:3rem" type="text" placeholder="from" bind:value={config.value_bottom_limit}>
						<div>,</div>
						<input style="width:3rem" type="text" placeholder="to" bind:value={config.value_top_limit}>
						<div>]</div>
					</div>
					<div class="params">
						<div>Max Code Lines</div>
						<input type="text" placeholder="eg. 30" bind:value={config.max_code_lines}>
					</div>

					<div style="padding-bottom: .2rem; font-weight: 800">Tree Generator</div>

					<div class="params">
						<div>Max Depth</div>
						<input type="text" placeholder="eg. 30" bind:value={config.max_depth}>
					</div>
					<div class="params">
						<div>Max Width</div>
						<input type="text" placeholder="eg. 30" bind:value={config.max_width}>
					</div>
					<div class="params">
						<div>Max Branch Depth</div>
						<input type="text" placeholder="eg. 30" bind:value={config.max_branch_depth}>
					</div>

					<div class="params">
						<div>Alpha Variables (%)</div>
						<input type="text" placeholder="eg. 30" bind:value={config.alpha_vars}>
					</div>

					<div style="padding-bottom: .2rem; font-weight: 800">Initial Knowledge</div>

					<div class="params">
						<button class="button" on:click={() => wildcardModalIsOpen = true}>
							<span class="material-icons md-18">edit</span>
							Wildcards
						</button>
						<button class="button" on:click={() => variableModalIsOpen = true}>
							<span class="material-icons md-18">edit</span>
							Variables
						</button>
					</div>

					<div class="modal" class:is-active={wildcardModalIsOpen}>
						<div class="modal-background"></div>
						<div class="modal-card">
							<header class="modal-card-head">
								<p class="modal-card-title">Wildcard code</p>
								<button class="delete" aria-label="close" on:click={() => wildcardModalIsOpen = false}></button>
							</header>
							<section class="modal-card-body">
								<!-- Content ... -->
								<div style="padding-bottom: 1rem;">All the edits are recorded.</div>
								<!-- <div class="wildcard-container" contenteditable="true"></div> -->
								
								{#each config.wildcards as wildcard}
								<div style="display: flex;justify-content: space-between;">
									<input style="background:#2e2e2e;width: 95%;" type="text" placeholder="int a = 10;" bind:value={wildcard}>
									<button style="margin-left: 0.5rem;" class="button" on:click={() => config.wildcards = config.wildcards.filter(code => code != wildcard)}>
										<span class="material-icons md-18" style="padding: 0;">delete</span>										
									</button>
								</div>
								{/each}
							</section>
							<footer class="modal-card-foot" style="justify-content: flex-end;">
								
								<button class="button" on:click={() => config.wildcards = [...config.wildcards, ""]}>
									<span class="material-icons md-18">add</span>
									Add Wildcard
								</button>
								<button class="button is-success" on:click={() => wildcardModalIsOpen = false}>Continue</button>
							</footer>
						</div>
					</div>
					<div class="modal" class:is-active={variableModalIsOpen}>
						<div class="modal-background"></div>
						<div class="modal-card">
							<header class="modal-card-head">
								<p class="modal-card-title">Initial Variables</p>
								<button class="delete" aria-label="close" on:click={() => variableModalIsOpen = false}></button>
							</header>
							<section class="modal-card-body">
								<!-- Content ... -->
								<div style="padding-bottom: 1rem;">All the edits are recorded.</div>
								<!-- <div class="wildcard-container" contenteditable="true"></div> -->
								
								{#each config.variables as variable}
								<div style="display: flex;justify-content: space-between;">
									<input style="background:#2e2e2e;width: 95%;" type="text" placeholder="eg. CongestionWnd" bind:value={variable}>
									<button style="margin-left: 0.5rem;" class="button" on:click={() => config.variables = config.variables.filter(code => code != variable)}>
										<span class="material-icons md-18" style="padding: 0;">delete</span>										
									</button>
								</div>
								{/each}
							</section>
							<footer class="modal-card-foot" style="justify-content: flex-end;">
								
								<button class="button" on:click={() => config.variables = [...config.variables, ""]}>
									<span class="material-icons md-18">add</span>
									Add Variable
								</button>
								<button class="button is-success" on:click={() => variableModalIsOpen = false}>Continue</button>
							</footer>
						</div>
					</div>
					{:else}
					<div style="padding-bottom: .2rem; font-weight: 800">Simulator</div>

					<div class="params">
						<div class="dropdown is-hoverable">							
							<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-mtu">
								Payload Size (bytes)
							</div>
							<div class="dropdown-menu" id="dropdown-mtu" role="menu">							
								<div class="dropdown-content">
								<div class="dropdown-item">
									Payload Size (or MTU) is the maximum payload length for a particular transmission media.
								</div>
								</div>
							</div>
						</div>
						<input type="text" placeholder="eg. 1500" bind:value={config.payload_size}>
					</div>
					<div class="params">
						<div class="dropdown is-hoverable">							
							<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-mtu">
								Simulation Time (s)
							</div>
							<div class="dropdown-menu" id="dropdown-mtu" role="menu">							
								<div class="dropdown-content">
								<div class="dropdown-item">
									How many seconds simulation for a single individual should be evaluated.
								</div>
								</div>
							</div>
						</div>
						<input type="text" placeholder="eg. 1500" bind:value={config.simulation_time}>
					</div>
					<div class="params">
						<div class="dropdown is-hoverable">							
							<div class="dropdown-trigger" aria-haspopup="true" aria-controls="dropdown-mtu">
								Multiple MTU Evaluation
							</div>
							<div class="dropdown-menu" id="dropdown-mtu" role="menu">							
								<div class="dropdown-content">
								<div class="dropdown-item">
									Evaluate Fitness as the sum of evaluation of multiple MTU sizes.
								</div>
								</div>
							</div>
						</div>
						<div style="display: flex;width: 1rem;top: .2rem;position: relative;">
							<input type="checkbox" placeholder="eg. 1500" bind:checked={config.multi_mtu}>
						</div>
					</div>

					<div class:disabled={!config.multi_mtu} style="padding-top:.5rem;">
						<div style="padding-bottom: .2rem; font-weight: 800">Multi MTU Settings</div>

						<div class="params">
							<div>MTU Range</div>
							<div>[</div>
							<input style="width:3rem" type="text" placeholder="from" bind:value={config.mtu_bottom_limit}>
							<div>,</div>
							<input style="width:3rem" type="text" placeholder="to" bind:value={config.mtu_upper_limit}>
							<div>]</div>
						</div>
						<div class="params">
							<div>MTU Step</div>
							<input type="text" placeholder="eg. 100" bind:value={config.mtu_step}>
						</div>

					</div>
					{/if}

				</div>
				

				<div class="params" style="justify-content: flex-start;">
					<span class="tab" class:tab-active={settingsDisplay == 'default'} 
						on:click={() => settingsDisplay = 'default'}>
						General</span>
					<span class="tab" class:tab-active={settingsDisplay == 'advanced'}  
						on:click={() => settingsDisplay = 'advanced'}>
						Advanced</span>
					<span class="tab"  class:tab-active={settingsDisplay == 'sim'} 
						on:click={() => settingsDisplay = 'sim'}>
						Sim</span>
				</div>
			</div>			
		</div>
		<div class="column is-four-fifths">
			<span style="padding: 1rem;padding-left:0;">
				🧬 Current Generation Individuals 🧬
			</span>
			<div class="individual-container" style="height:23rem;">
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
		<div class="column" style="text-align: left;padding-left: 1.8rem;display:flex;justify-content:space-evenly">
			
			<span>🧬 <b>Generation:</b> 
				<span class="span-value">{generationNumber || 'n.a.'}</span> 
				/ {config.gen}</span>

			{#if !calculatingBaseline}
			<span>🏁 <b>Baseline:</b> 
				<span class="span-value">
					{baseline?.toFixed(2) || "n.a."}
				</span> Mbit/s</span>
			{:else}
			<Rainbow size="30" color="#FEFEFE" unit="px" duration="2s"></Rainbow>
			{/if}

			<span>🥇 <b>Current Best:</b> 
				<span class="span-value">{currentBest?.toFixed(2) || "n.a."}</span> 
				Mbit/s</span>

			<span style="padding-right: 1rem">💡 <b>Gain:</b> 
				<span class="span-value">{((((currentBest ?? 0)/(baseline || 1))-1)*100).toFixed(2)}</span>
				%</span>
		</div>
		<div class="column is-two-fifths" style="margin: auto;">			
			<div style="display: flex; align-items: center; justify-content: space-between;">
				<div>{((current_gen.length/config.pop)*100).toFixed(0)}%</div>
				<div class="progress-bar" style="width: 89%;">
					<div class="progress-bar-thumb" style="width: {(current_gen.length/config.pop)*100}%;"></div>
				</div>
			</div>
		</div>
	</div>


	<div class="columns">
		<div class="column is-half">
			<span style="padding: 1rem;padding-left:0;">
				📈 Fitness Chart
			</span>
			<div style="padding: 2rem;padding-top:0.5rem;">
				<canvas id="fitnessChart"></canvas>
			</div>
		</div>
		<div class="column is-one-fourth">
			<div style="display: flex;justify-content:center;align-items:center;">
				<span>
					🏆 Hall of Fame Individuals 🏆
				</span>
			</div>
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
					document.getElementById('cons-container').style.height = "27rem";
					fullScreenTerminal = true;
				}
			}}>
				
				{#if fullScreenTerminal}
					<span class="material-icons">
						close_fullscreen
					</span>
					Collapse
				{:else}
					<span class="material-icons">
						open_in_full
					</span>
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
	.disabled {
		opacity: 0.5;
		pointer-events: none;
	}
	.tab {
		padding: 0.25rem 1rem;
		cursor: pointer;
		background:#2a2a2a;
		font-weight: 600;
	}
	.tab:hover {
		background:#262626;
		color: #fff;
	}
	.tab-active {
		background:#262626;
		color: #fff;
	}
	.tab-active:hover {
		background:#2a2a2a;
	}
	.progress-bar {
		background-color: #3c3c3c;
		border-radius: 1rem;
		height: .4rem;
		margin-right: 1rem;
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
		width: 4.5rem;
		text-align: right;
		padding: 0.2rem 0.5rem;
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
		/* margin-right: 2.5rem; */
		height: 20rem;
		overflow-y: auto;
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