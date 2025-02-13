/** @odoo-module **/
import { useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/views/utils";

const printZPLService = {
	dependencies: ["orm", "bus_service"],
	async start(env, { orm, bus_service }) {
		// set sessionStorage client_id to identify the client tab browser
		let sessionStorage = window.sessionStorage;
		sessionStorage.setItem("client_id", uuid());
		let clientId = sessionStorage.getItem("client_id");
		console.log("BrowserPrint", BrowserPrint);
		// const devices = [];
		// let selected_device = null;
		// BrowserPrint.getDefaultDevice(
		// 	"printer",
		// 	function (device) {
		// 		//Add device to list of devices and to html select element
		// 		selected_device = device;
		// 		devices.push(device);
		// 	},
		// 	function (error) {
		// 		console.log(error);
		// 	}
		// );

		bus_service.addChannel(`nuprod_print_browser`);
		bus_service.addEventListener("notification", async (message) => {
			const proms = message.detail.map((detail) => {
				const datas = detail.payload;

				switch (detail.type) {
					case "client_id_print_zpl":
						console.log("client_id_print_zpl", datas);
						console.log("Quentin client_id", clientId);

						if (datas.client_id === clientId) {
							const devices = [];
							BrowserPrint.getDefaultDevice(
								"printer",
								function (device) {
									devices.push(device);
									console.log(devices);

									device.send(
										datas.render,
										function (success) {
											console.log("Sent to printer");
										},
										function (error) {
											console.error("Error:" + error);
										}
									);
								},
								function (error) {
									console.error(error);
								}
							);
							// if (selected_device) {
							// 	selected_device.send(
							// 		datas.render,
							// 		function (success) {
							// 			console.log("Sent to printer");
							// 		},
							// 		function (error) {
							// 			console.log("Error:" + error);
							// 		}
							// 	);
							// }
						}
						break;
				}
			});

			await Promise.all(proms);
		});

		return printZPLService;
	},
};

registry.category("services").add("print_zpl_browser", printZPLService);

/**
 *
 * @returns {ReturnType<typeof printZPLService.start>}
 */
export function useprintZPLService() {
	return useState(useService("print_zpl_browser"));
}
