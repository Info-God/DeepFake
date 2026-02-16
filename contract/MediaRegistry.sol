// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MediaRegistry {
    struct Media {
        string hash;
        string description;
        address uploader;
        uint256 timestamp;
    }

    mapping(string => Media) public mediaList;

    event MediaRegistered(string hash, string description, address uploader, uint256 timestamp);

    function registerMedia(string memory _hash, string memory _description) public {
        require(bytes(mediaList[_hash].hash).length == 0, "Already registered");

        mediaList[_hash] = Media({
            hash: _hash,
            description: _description,
            uploader: msg.sender,
            timestamp: block.timestamp
        });

        emit MediaRegistered(_hash, _description, msg.sender, block.timestamp);
    }

    function verifyMedia(string memory _hash) public view returns (bool, string memory, address, uint256) {
        if (bytes(mediaList[_hash].hash).length == 0) {
            return (false, "", address(0), 0);
        }
        Media memory m = mediaList[_hash];
        return (true, m.description, m.uploader, m.timestamp);
    }
}
