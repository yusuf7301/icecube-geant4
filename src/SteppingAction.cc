#include "SteppingAction.hh"
#include "OutputManager.hh"

#include "G4Step.hh"
#include "G4Track.hh"
#include "G4OpticalPhoton.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VProcess.hh"

SteppingAction::SteppingAction() : G4UserSteppingAction() {}
SteppingAction::~SteppingAction() {}

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  G4Track* track = step->GetTrack();
  // Optik fotonlar en sık gelen adımlardır, hemen çık
  if (track->GetDefinition() == G4OpticalPhoton::Definition()) return;

  G4StepPoint* pre  = step->GetPreStepPoint();
  G4StepPoint* post = step->GetPostStepPoint();

  // Sadece buz içindeki (dünya hacmi dışındaki) adımlar
  if (pre->GetPhysicalVolume()->GetName() == "World") return;

  auto* out = OutputManager::Instance();
  out->AddEdep(step->GetTotalEnergyDeposit());

  if (track->GetTrackID() != 1) return; // Bundan sonrası yalnızca birincil müon için

  const G4VProcess* proc = post->GetProcessDefinedStep();
  out->AddMuonStep(post->GetPosition(), pre->GetKineticEnergy(), post->GetKineticEnergy(),
                   step->GetTotalEnergyDeposit(), step->GetStepLength(),
                   proc ? proc->GetProcessName() : "none");

  // Müon buzdan çıkıyor mu?
  G4VPhysicalVolume* next = post->GetPhysicalVolume();
  if (!next || next->GetName() == "World") out->SetMuonExitEnergy(post->GetKineticEnergy());
}
