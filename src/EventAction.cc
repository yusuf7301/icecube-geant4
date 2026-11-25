#include "EventAction.hh"
#include "Config.hh"
#include "OutputManager.hh"

#include "G4Event.hh"
#include "G4PrimaryVertex.hh"
#include "G4PrimaryParticle.hh"

EventAction::EventAction() : G4UserEventAction() {}
EventAction::~EventAction() {}

void EventAction::BeginOfEventAction(const G4Event* event)
{
  G4int id = event->GetEventID();
  // Fotonlar sadece ilk birkaç olay için tek tek yazılır (1 TeV müon ~10^5-10^6 foton üretir)
  OutputManager::Instance()->BeginEvent(id, id < Config::Instance()->photonSaveEvents);
}

void EventAction::EndOfEventAction(const G4Event* event)
{
  G4PrimaryVertex* vertex = event->GetPrimaryVertex();
  G4PrimaryParticle* muon = vertex->GetPrimary();
  OutputManager::Instance()->EndEvent(muon->GetKineticEnergy(), vertex->GetPosition(),
                                      muon->GetMomentumDirection());
}
