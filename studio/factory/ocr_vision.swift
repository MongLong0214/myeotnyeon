// Offline native OCR. Input/output: one JSON object per image; normalized boxes
// use top-left coordinates, matching the Python subtitle band contract.
import Foundation
import Vision
import AppKit
let outputLock = NSLock()
let queue = OperationQueue()
queue.maxConcurrentOperationCount = Int(ProcessInfo.processInfo.environment["REVIEW_OCR_WORKERS"] ?? "1") ?? 1
func process(_ line: String) {
    var output: [String: Any] = [:]
    do {
        let input = try JSONSerialization.jsonObject(with: Data(line.utf8)) as! [String: Any]
        output["frame"] = input["frame"]
        let url = URL(fileURLWithPath: input["path"] as! String)
        if input["only_people"] as? Bool == true {
            let people = VNDetectHumanRectanglesRequest()
            people.upperBodyOnly = false
            try VNImageRequestHandler(url: url).perform([people])
            output["people"] = (people.results ?? []).count
            output["boxes"] = []
        } else {
            let request = VNRecognizeTextRequest()
            request.recognitionLevel = .accurate
            request.recognitionLanguages = ["ko-KR", "en-US"]
            request.usesLanguageCorrection = false
            request.usesCPUOnly = true
            try VNImageRequestHandler(url: url).perform([request])
            output["boxes"] = (request.results ?? []).compactMap { observation -> [String: Any]? in
                guard let candidate = observation.topCandidates(1).first else { return nil }
                let b = observation.boundingBox
                return ["text": candidate.string, "confidence": candidate.confidence,
                        "x": b.minX, "y": 1-b.maxY, "w": b.width, "h": b.height]
            }
        }
    } catch { output["error"] = String(describing: error); output["boxes"] = [] }
    let data = try! JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
    outputLock.lock()
    print(String(data: data, encoding: .utf8)!)
    outputLock.unlock()
}
while let line = readLine() {
    queue.addOperation { autoreleasepool { process(line) } }
}
queue.waitUntilAllOperationsAreFinished()
