#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"
#include "G4Threading.hh"

#include "DetectorConstruction.hh"
#include "ActionInitialization.hh"
#include "Config.hh"
#include "QBBC.hh"               // Standart fizik listesi (müon, elektromanyetik, hadronik)
#include "G4OpticalPhysics.hh"   // Cherenkov, soğurma, Rayleigh, sınır süreçleri
#include "G4OpticalParameters.hh"
#include "G4EmParameters.hh"
#include "G4SystemOfUnits.hh"

int main(int argc, char** argv)
{
    // Kullanım:  ./sim               -> görsel arayüz (vis.mac)
    //            ./sim run1TeV.mac   -> batch modu
    //            ./sim run1TeV.mac 4 -> batch modu, 4 thread
    G4UIExecutive* ui = nullptr;
    if (argc == 1) ui = new G4UIExecutive(argc, argv);

    // 1. Run Manager oluşturma (çok thread'li)
    auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Default);
    G4int nThreads = (argc > 2) ? std::atoi(argv[2]) : G4Threading::G4GetNumberOfCores();
    runManager->SetNumberOfThreads(nThreads);

    // /icecube/... komutları makrodan önce tanımlı olmalı
    Config::Instance();

    // 2. Fizik listesi: QBBC + optik fizik
    auto* physicsList = new QBBC;
    physicsList->RegisterPhysics(new G4OpticalPhysics());

    // EM fizik tabloları varsayılan olarak yalnızca 100 TeV'e kadar hesaplanır; 100 TeV müon tablo
    // sınırında radyatif kayıpları eksik verir. Tablolar 10 PeV'e genişletilir.
    G4EmParameters::Instance()->SetMaxEnergy(10*PeV);

    auto* optical = G4OpticalParameters::Instance();
    optical->SetCerenkovMaxPhotonsPerStep(500);       // Adım başına en fazla foton -> müon adım boyu ~1.5 cm
    optical->SetCerenkovMaxBetaChange(10.0);
    optical->SetCerenkovTrackSecondariesFirst(true);
    optical->SetProcessActivation("Scintillation", false); // Buz sintilasyon yapmaz
    optical->SetProcessActivation("OpWLS", false);
    optical->SetProcessActivation("OpWLS2", false);
    // Rayleigh ve Mie ikisi de kurulur; buz modeli makroda /process/inactivate ile seçilir

    // 3. Zorunlu sınıfları sisteme tanıtma
    runManager->SetUserInitialization(new DetectorConstruction()); // Geometri
    runManager->SetUserInitialization(physicsList);                // Fizik
    runManager->SetUserInitialization(new ActionInitialization()); // Eylemler

    // Simülasyon motoru makrodaki /run/initialize ile başlatılır. Böylece geometri
    // ayarları (ör. /icecube/stringSpacing) başlatmadan önce değiştirilebilir.
    // /run/initialize olmadan /run/beamOn çalışmaz.

    G4VisManager* visManager = new G4VisExecutive;
    visManager->Initialize();

    // 4. Kullanıcı komutlarını dinlemeye başla
    G4UImanager* UImanager = G4UImanager::GetUIpointer();

    if (ui) {
        UImanager->ApplyCommand("/control/execute vis.mac");
        ui->SessionStart();
        delete ui;
    } else {
        // Batch (toplu iş) modunda makro dosyasını çalıştır.
        G4String command = "/control/execute ";
        G4String fileName = argv[1];
        UImanager->ApplyCommand(command + fileName);
    }

    delete visManager;
    delete runManager;
    return 0;
}
