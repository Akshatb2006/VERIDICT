const hre = require("hardhat");

async function main() {
    console.log("🚀 Deploying VerifierContract to Flare Coston2...\n");

    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying with account:", deployer.address);

    // Get balance
    const balance = await hre.ethers.provider.getBalance(deployer.address);
    console.log("Account balance:", hre.ethers.formatEther(balance), "C2FLR\n");

    // Deploy contract
    console.log("Deploying VerifierContract...");
    const VerifierContract = await hre.ethers.getContractFactory("VerifierContract");
    const verifier = await VerifierContract.deploy();

    await verifier.waitForDeployment();

    const address = await verifier.getAddress();
    console.log("✅ VerifierContract deployed to:", address);

    // Test contract
    console.log("\n📊 Testing contract...");
    const stats = await verifier.getStatistics();
    console.log("Initial statistics:", {
        total: stats[0].toString(),
        valid: stats[1].toString(),
        invalid: stats[2].toString(),
        successRate: stats[3].toString() + " bps"
    });

    console.log("\n📝 Configuration:");
    console.log("Add this to your .env file:");
    console.log(`VERIFIER_CONTRACT_ADDRESS=${address}`);

    console.log("\n🔍 Verify on explorer:");
    console.log(`https://coston2-explorer.flare.network/address/${address}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
