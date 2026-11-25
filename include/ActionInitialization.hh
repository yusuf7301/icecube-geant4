#ifndef ActionInitialization_h
#define ActionInitialization_h 1

#include "G4VUserActionInitialization.hh"

class ActionInitialization : public G4VUserActionInitialization
{
  public:
    ActionInitialization();
    virtual ~ActionInitialization();

    virtual void BuildForMaster() const; // Ana thread: sadece RunAction (dosya birleştirme)
    virtual void Build() const;          // İşçi thread'ler için eylemleri tanımlar
};

#endif
