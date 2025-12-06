require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
    solidity: {
        version: "0.8.20",
        settings: {
            optimizer: {
                enabled: true,
                runs: 200
            }
        }
    },
    networks: {
        coston2: {
            url: process.env.FLARE_RPC_URL || "https://coston2-api.flare.network/ext/C/rpc",
            chainId: 114,
            accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
            gas: 3000000,
            gasPrice: 25000000000  // 25 gwei
        }
    },
    etherscan: {
        apiKey: {
            coston2: "flare"  // Dummy API key
        },
        customChains: [
            {
                network: "coston2",
                chainId: 114,
                urls: {
                    apiURL: "https://coston2-explorer.flare.network/api",
                    browserURL: "https://coston2-explorer.flare.network"
                }
            }
        ]
    }
};
