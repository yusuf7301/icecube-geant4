#include "StackingAction.hh"
#include "OutputManager.hh"

#include "G4Track.hh"
#include "G4OpticalPhoton.hh"
#include "G4VProcess.hh"

StackingAction::StackingAction() : G4UserStackingAction() {}
StackingAction::~StackingAction() {}

G4ClassificationOfNewTrack StackingAction::ClassifyNewTrack(const G4Track* track)
{
  if (track->GetDefinition() == G4OpticalPhoton::Definition()) {
    const G4VProcess* creator = track->GetCreatorProcess();
    if (creator && creator->GetProcessName() == "Cerenkov") {
      OutputManager::Instance()->AddPhoton(track->GetParentID(), track->GetPosition(),
                                           track->GetMomentumDirection(),
                                           track->GetTotalEnergy(), track->GetGlobalTime());
    }
  }
  return fUrgent;
}
