
const anotherButton = document.getElementById("another");
const completeButton = document.getElementById("complete-mission");
const totalPointsDisplay = document.getElementById("total-points");
const completionMessage = document.getElementById("completion-message");

// Load saved points
let totalPoints = Number(localStorage.getItem("touchgrassPoints")) || 0;
let currentMissionPoints = 25;
let missionCompleted = false;

updateTotalPoints();

// Update total points
function updateTotalPoints() {
    totalPointsDisplay.textContent = `⭐ ${totalPoints} pts`;
}

// Display a mission
function displayMission(data) {
    document.getElementById("mission-title").textContent = data.mission;

    const instructions = document.querySelectorAll("#task li");

    instructions.forEach((item, index) => {
        item.textContent = data.instructions[index];
    });

    document.getElementById("mission-time").textContent =
        `${data.time_minutes} MIN`;

    document.getElementById("mission-points").textContent =
        `${data.points} points`;

    currentMissionPoints = data.points;
}

// Restore saved mission when page loads
const savedMission = localStorage.getItem("touchgrassMission");

if (savedMission) {
    try {
        const missionData = JSON.parse(savedMission);

        displayMission(missionData);

        missionCompleted =
            localStorage.getItem("touchgrassCompleted") === "true";

        if (missionCompleted) {
            completeButton.disabled = true;
            completeButton.textContent = "Mission completed ✓";
            completionMessage.textContent =
                "You've already completed this mission!";
        }

    } catch (error) {
        console.error("Could not restore mission:", error);
        localStorage.removeItem("touchgrassMission");
        localStorage.removeItem("touchgrassCompleted");
    }
}

// Complete mission
completeButton.addEventListener("click", function () {

    if (missionCompleted) {
        return;
    }

    missionCompleted = true;

    // Save completion status
    localStorage.setItem("touchgrassCompleted", "true");

    // Award points
    totalPoints += currentMissionPoints;

    // Save points
    localStorage.setItem("touchgrassPoints", totalPoints);

    updateTotalPoints();

    completionMessage.textContent =
        `Mission complete! You earned ${currentMissionPoints} points! 🎉`;

    completeButton.disabled = true;
    completeButton.textContent = "Mission completed ✓";
});

// Generate another mission
anotherButton.addEventListener("click", async function () {

    anotherButton.disabled = true;
    anotherButton.textContent = "Generating mission...";
    completeButton.disabled = true;

    try {
        const response = await fetch("/api/mission");

        if (!response.ok) {
            throw new Error("Mission generation failed");
        }

        const data = await response.json();

        // Display new mission
        displayMission(data);

        // Save new mission
        localStorage.setItem(
            "touchgrassMission",
            JSON.stringify(data)
        );

        // Reset completion status
        missionCompleted = false;
        localStorage.setItem("touchgrassCompleted", "false");

        completeButton.disabled = false;
        completeButton.textContent = "I've completed this mission ✓";

        completionMessage.textContent = "";

    } catch (error) {
        console.error(error);

        completionMessage.textContent =
            "Couldn't generate a mission. Please try again.";

        completeButton.disabled = missionCompleted;

    } finally {
        anotherButton.disabled = false;
        anotherButton.textContent = "Find another mission";
    }
});
