#include "ActionInitialization.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "EventAction.hh"
#include "SteppingAction.hh"
#include "StackingAction.hh"

ActionInitialization::ActionInitialization() : G4VUserActionInitialization() {}
ActionInitialization::~ActionInitialization() {}

void ActionInitialization::BuildForMaster() const
{
  SetUserAction(new RunAction);
}

void ActionInitialization::Build() const
{
  SetUserAction(new PrimaryGeneratorAction); // AGN yönünden gelen müon
  SetUserAction(new RunAction);              // CSV dosyaları
  SetUserAction(new EventAction);            // Olay özetleri
  SetUserAction(new SteppingAction);         // Müon enerji kaybı
  SetUserAction(new StackingAction);         // Cherenkov fotonları
}
